import json
import urllib.error
import urllib.request

import streamlit as st


def api_request(
    base_url: str,
    method: str,
    path: str,
    user_id: str,
    payload: dict | None = None,
    file: object | None = None,
) -> dict:
    headers = {"X-User-Id": user_id}
    body: bytes | None = None
    if file is not None:
        uploaded = file
        boundary = "----legalragboundary"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        body = (
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{uploaded.name}"\r\n'
                f"Content-Type: {uploaded.type or 'application/octet-stream'}\r\n\r\n"
            ).encode()
            + uploaded.getvalue()
            + f"\r\n--{boundary}--\r\n".encode()
        )
    elif payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed ({error.code}): {detail}") from error


def main() -> None:
    st.set_page_config(page_title="Privacy-Preserving Legal RAG", layout="wide")
    st.title("Privacy-Preserving Legal RAG")
    st.caption("Research support only — not legal advice.")
    base_url = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")
    user_id = st.sidebar.text_input("User ID", value="demo-user")
    if not user_id:
        st.info("Enter a known user ID to continue.")
        return

    try:
        matters = api_request(base_url, "GET", "/matters", user_id)["matters"]
    except RuntimeError as error:
        if "API request failed (401)" in str(error):
            st.error(
                f"User '{user_id}' is not registered in the local API. "
                "Run `python -m app.bootstrap` from the project directory, then refresh."
            )
        else:
            st.error(str(error))
        st.stop()
    matter_options = {item["matter_id"]: item for item in matters}
    selected = st.sidebar.selectbox("Matter", ["All authorized matters", *matter_options])
    new_matter = st.sidebar.text_input("New matter ID", key="new_matter")
    if st.sidebar.button("Create matter") and new_matter:
        try:
            api_request(base_url, "POST", "/matters", user_id, {"matter_id": new_matter})
            st.rerun()
        except RuntimeError as error:
            st.error(str(error))

    st.subheader("Ask a question")
    question = st.text_area("Question", placeholder="What evidence supports this claim?")
    public = st.checkbox("Include public legal sources", value=True)
    if st.button("Search and answer", type="primary") and question.strip():
        scope = [] if selected == "All authorized matters" else [selected]
        try:
            result = api_request(
                base_url,
                "POST",
                "/query",
                user_id,
                {"question": question, "scope": {"public": public, "matter_ids": scope}},
            )
            st.session_state["last_result"] = result
        except RuntimeError as error:
            st.error(str(error))

    result = st.session_state.get("last_result")
    if result:
        if result.get("abstained"):
            st.warning(
                "The system abstained because the evidence was insufficient or citations failed."
            )
        elif result.get("answer"):
            st.markdown(result["answer"])
        st.subheader("Authorized sources")
        for evidence in result.get("evidence", []):
            label = evidence.get("matter_id") or "public"
            st.write(
                f"**{label}** · {evidence.get('document_id')} · "
                f"page {evidence.get('page', 'unknown')} · paragraph {evidence.get('paragraph', 'unknown')}"
            )
        with st.expander("Evidence-only prompt"):
            st.code(result.get("prompt", ""), language="text")

    st.subheader("Matter documents")
    if selected != "All authorized matters":
        try:
            documents = api_request(base_url, "GET", f"/matters/{selected}/documents", user_id)[
                "documents"
            ]
            st.dataframe(documents, use_container_width=True)
            upload = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
            if upload and st.button("Index document"):
                result = api_request(
                    base_url, "POST", f"/matters/{selected}/documents", user_id, file=upload
                )
                st.success(f"Document status: {result['status']}")
        except RuntimeError as error:
            st.error(str(error))

    st.subheader("Audit")
    try:
        audit = api_request(base_url, "GET", "/audit", user_id)["events"]
        st.dataframe(audit, use_container_width=True)
    except RuntimeError as error:
        st.error(str(error))


if __name__ == "__main__":
    main()
