$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$outputDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputPath = Join-Path $outputDirectory "keyword-to-cited-answer.png"
$width = 3300
$height = 2100

$bitmap = [System.Drawing.Bitmap]::new(
    $width,
    $height,
    [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
)
$bitmap.SetResolution(300, 300)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$graphics.Clear([System.Drawing.Color]::White)

$fontTitle = [System.Drawing.Font]::new("Arial", 54, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fontSubtitle = [System.Drawing.Font]::new("Arial", 29, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$fontPanel = [System.Drawing.Font]::new("Arial", 34, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fontCard = [System.Drawing.Font]::new("Arial", 29, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
$fontBody = [System.Drawing.Font]::new("Arial", 25, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$fontSmall = [System.Drawing.Font]::new("Arial", 22, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
$fontExample = [System.Drawing.Font]::new("Arial", 27, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)

function ConvertTo-Color {
    param([string]$Hex)
    return [System.Drawing.ColorTranslator]::FromHtml($Hex)
}

function Draw-Text {
    param(
        [string]$Text,
        [single]$X,
        [single]$Y,
        [System.Drawing.Font]$Font,
        [string]$Color = "#183247"
    )
    $brush = [System.Drawing.SolidBrush]::new((ConvertTo-Color $Color))
    $graphics.DrawString($Text, $Font, $brush, $X, $Y)
    $brush.Dispose()
}

function Draw-Lines {
    param(
        [string[]]$Lines,
        [single]$X,
        [single]$Y,
        [System.Drawing.Font]$Font,
        [single]$LineGap = 38,
        [string]$Color = "#34495B"
    )
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        Draw-Text -Text $Lines[$i] -X $X -Y ($Y + $i * $LineGap) -Font $Font -Color $Color
    }
}

function New-RoundedPath {
    param([single]$X, [single]$Y, [single]$W, [single]$H, [single]$Radius)
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $d = $Radius * 2
    $path.AddArc($X, $Y, $d, $d, 180, 90)
    $path.AddArc(($X + $W - $d), $Y, $d, $d, 270, 90)
    $path.AddArc(($X + $W - $d), ($Y + $H - $d), $d, $d, 0, 90)
    $path.AddArc($X, ($Y + $H - $d), $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Draw-Card {
    param(
        [single]$X, [single]$Y, [single]$W, [single]$H,
        [string]$Fill = "#FFFFFF",
        [string]$Stroke = "#D4DEE8",
        [single]$Radius = 26,
        [single]$StrokeWidth = 3
    )
    $path = New-RoundedPath -X $X -Y $Y -W $W -H $H -Radius $Radius
    $fillBrush = [System.Drawing.SolidBrush]::new((ConvertTo-Color $Fill))
    $strokePen = [System.Drawing.Pen]::new((ConvertTo-Color $Stroke), $StrokeWidth)
    $graphics.FillPath($fillBrush, $path)
    $graphics.DrawPath($strokePen, $path)
    $fillBrush.Dispose()
    $strokePen.Dispose()
    $path.Dispose()
}

function Draw-Arrow {
    param(
        [single]$X1, [single]$Y1, [single]$X2, [single]$Y2,
        [string]$Color = "#71879A",
        [single]$StrokeWidth = 6
    )
    $dx = $X2 - $X1
    $dy = $Y2 - $Y1
    $length = [Math]::Sqrt(($dx * $dx) + ($dy * $dy))
    if ($length -lt 1) {
        return
    }
    $unitX = $dx / $length
    $unitY = $dy / $length
    $perpX = -$unitY
    $perpY = $unitX
    $headLength = [Math]::Min(20, $length * 0.45)
    $headWidth = 13
    $baseX = $X2 - ($unitX * $headLength)
    $baseY = $Y2 - ($unitY * $headLength)
    $pen = [System.Drawing.Pen]::new((ConvertTo-Color $Color), $StrokeWidth)
    $graphics.DrawLine($pen, $X1, $Y1, $baseX, $baseY)
    $points = [System.Drawing.PointF[]]@(
        [System.Drawing.PointF]::new($X2, $Y2),
        [System.Drawing.PointF]::new(($baseX + ($perpX * $headWidth)), ($baseY + ($perpY * $headWidth))),
        [System.Drawing.PointF]::new(($baseX - ($perpX * $headWidth)), ($baseY - ($perpY * $headWidth)))
    )
    $headBrush = [System.Drawing.SolidBrush]::new((ConvertTo-Color $Color))
    $graphics.FillPolygon($headBrush, $points)
    $headBrush.Dispose()
    $pen.Dispose()
}

function Draw-Stage {
    param(
        [int]$X,
        [string]$Number,
        [string]$Title,
        [string]$Accent
    )
    $circle = [System.Drawing.SolidBrush]::new((ConvertTo-Color $Accent))
    $graphics.FillEllipse($circle, $X, 275, 58, 58)
    $circle.Dispose()
    Draw-Text -Text $Number -X ($X + 18) -Y 283 -Font $fontCard -Color "#FFFFFF"
    Draw-Text -Text $Title -X ($X + 78) -Y 281 -Font $fontPanel -Color "#183247"
}

function Draw-CardTitle {
    param([string]$Text, [int]$X, [int]$Y, [string]$Color = "#183247")
    Draw-Text -Text $Text -X $X -Y $Y -Font $fontCard -Color $Color
}

# Header
Draw-Text -Text "How a query becomes a cited legal answer" -X 78 -Y 48 -Font $fontTitle -Color "#102F48"
Draw-Text -Text "Current prototype: local hybrid retrieval, matter-scoped evidence, and code-validated citations" -X 82 -Y 126 -Font $fontSubtitle -Color "#52697C"

# Three stage panels
$panelY = 245
$panelH = 1405
$panelW = 996
$x1 = 75
$x2 = 1152
$x3 = 2229
Draw-Card -X $x1 -Y $panelY -W $panelW -H $panelH -Fill "#F5F8FB" -Stroke "#CCD8E3" -Radius 32 -StrokeWidth 3
Draw-Card -X $x2 -Y $panelY -W $panelW -H $panelH -Fill "#F5F8FB" -Stroke "#CCD8E3" -Radius 32 -StrokeWidth 3
Draw-Card -X $x3 -Y $panelY -W $panelW -H $panelH -Fill "#F5F8FB" -Stroke "#CCD8E3" -Radius 32 -StrokeWidth 3

Draw-Stage -X ($x1 + 34) -Number "1" -Title "Query & retrieval" -Accent "#356C9A"
Draw-Stage -X ($x2 + 34) -Number "2" -Title "Matter authorization" -Accent "#B77920"
Draw-Stage -X ($x3 + 34) -Number "3" -Title "Answer & validation" -Accent "#168477"
Draw-Arrow -X1 ($x1 + $panelW + 7) -Y1 306 -X2 ($x2 - 8) -Y2 306 -Color "#557188" -StrokeWidth 7
Draw-Arrow -X1 ($x2 + $panelW + 7) -Y1 306 -X2 ($x3 - 8) -Y2 306 -Color "#557188" -StrokeWidth 7

# Stage 1: input and retrieval branches
$inX = $x1 + 32
Draw-Card -X $inX -Y 365 -W 932 -H 175 -Fill "#FFFFFF" -Stroke "#B9C9D8"
Draw-CardTitle -Text "INPUT QUESTION" -X ($inX + 28) -Y 386 -Color "#356C9A"
Draw-Text -Text "Question: What was the replacement deadline for the damaged chairs?" -X ($inX + 28) -Y 427 -Font $fontBody -Color "#183247"
Draw-Text -Text "User identity + selected matter IDs define the search scope." -X ($inX + 28) -Y 477 -Font $fontSmall -Color "#52697C"

$branchY = 590
$branchH = 410
$branchW = 442
$lexX = $inX
$denseX = $inX + 490
Draw-Arrow -X1 ($x1 + 498) -Y1 540 -X2 ($lexX + 220) -Y2 ($branchY - 8) -Color "#5D86A5" -StrokeWidth 5
Draw-Arrow -X1 ($x1 + 498) -Y1 540 -X2 ($denseX + 220) -Y2 ($branchY - 8) -Color "#4B9A91" -StrokeWidth 5
Draw-Card -X $lexX -Y $branchY -W $branchW -H $branchH -Fill "#EDF4FA" -Stroke "#8EB2CC"
Draw-CardTitle -Text "LEXICAL · SQLITE FTS5" -X ($lexX + 22) -Y ($branchY + 24) -Color "#285F8F"
Draw-Lines -Lines @(
    "Lowercase alphanumeric tokens",
    "OR-joined FTS5 MATCH query",
    "BM25 ranks matching chunks",
    "Example terms:",
    "replacement · deadline",
    "damaged · chairs",
    "Token matching; no separate",
    "keyphrase extraction model."
) -X ($lexX + 22) -Y ($branchY + 75) -Font $fontSmall -LineGap 38

Draw-Card -X $denseX -Y $branchY -W $branchW -H $branchH -Fill "#EAF6F4" -Stroke "#80B8B0"
Draw-CardTitle -Text "DENSE · LOCAL HASH" -X ($denseX + 22) -Y ($branchY + 24) -Color "#19776F"
Draw-Lines -Lines @(
    "Same question → deterministic",
    "384-dimensional token-hash vector",
    "Cosine similarity ranks private",
    "passage vectors.",
    "",
    "Offline hash baseline;",
    "not a trained semantic model."
) -X ($denseX + 22) -Y ($branchY + 75) -Font $fontSmall -LineGap 41

$hybridY = 1090
$hybridH = 480
Draw-Arrow -X1 ($lexX + 221) -Y1 ($branchY + $branchH) -X2 ($x1 + 497) -Y2 ($hybridY - 8) -Color "#5D86A5" -StrokeWidth 5
Draw-Arrow -X1 ($denseX + 221) -Y1 ($branchY + $branchH) -X2 ($x1 + 497) -Y2 ($hybridY - 8) -Color "#4B9A91" -StrokeWidth 5
Draw-Card -X $inX -Y $hybridY -W 932 -H $hybridH -Fill "#FFFFFF" -Stroke "#B9C9D8"
Draw-CardTitle -Text "HYBRID CANDIDATE RANKING" -X ($inX + 28) -Y ($hybridY + 24) -Color "#183247"
Draw-Lines -Lines @(
    "Private: α × dense + (1−α) × normalized lexical score",
    "Default α = 0.7 (HYBRID_ALPHA).",
    "",
    "Public: query expansion + at least 2 topic-term overlaps;",
    "lexical-heavy score = 0.1 × dense + 0.9 × lexical.",
    "",
    "Top-k candidates move to matter authorization."
) -X ($inX + 28) -Y ($hybridY + 78) -Font $fontBody -LineGap 48

# Stage 2: matter scope and defense in depth
$midX = $x2 + 32
Draw-Card -X $midX -Y 390 -W 932 -H 330 -Fill "#FFF8EB" -Stroke "#D9B36F"
Draw-CardTitle -Text "QUERY-TIME SCOPE FILTER" -X ($midX + 28) -Y 416 -Color "#966014"
Draw-Lines -Lines @(
    "Requested matter IDs are intersected with the",
    "user’s permission snapshot.",
    "SQL search is restricted to authorized matter IDs.",
    "Public sources are included only when enabled.",
    "Unauthorized private chunks are excluded before ranking."
) -X ($midX + 28) -Y 473 -Font $fontBody -LineGap 46

Draw-Arrow -X1 ($x2 + 498) -Y1 720 -X2 ($x2 + 498) -Y2 765 -Color "#B77920" -StrokeWidth 6
Draw-Card -X $midX -Y 775 -W 932 -H 355 -Fill "#FFFFFF" -Stroke "#D9B36F"
Draw-CardTitle -Text "SECOND CHECK + POLICY VERSION" -X ($midX + 28) -Y 800 -Color "#966014"
Draw-Lines -Lines @(
    "Application code checks every retrieved chunk",
    "against the same permission snapshot.",
    "The policy version is read again before prompt",
    "assembly. If permissions changed, the request aborts.",
    "",
    "This check is enforced in code, not just in the prompt."
) -X ($midX + 28) -Y 858 -Font $fontBody -LineGap 43

Draw-Arrow -X1 ($x2 + 498) -Y1 1130 -X2 ($x2 + 498) -Y2 1175 -Color "#B77920" -StrokeWidth 6
Draw-Card -X $midX -Y 1185 -W 932 -H 360 -Fill "#FDFEFF" -Stroke "#D9B36F"
Draw-CardTitle -Text "AUTHORIZED EVIDENCE CONTEXT" -X ($midX + 28) -Y 1210 -Color "#966014"
Draw-Lines -Lines @(
    "Only allowed passages proceed.",
    "Text and source, page, and paragraph metadata are kept.",
    "Evidence is numbered [1] … [k] for the prompt.",
    "",
    "Context ⊆ public sources ∪ authorized matters."
) -X ($midX + 28) -Y 1268 -Font $fontBody -LineGap 47

# Stage 3: prompt, local generation, and citation checking
$outX = $x3 + 32
Draw-Card -X $outX -Y 385 -W 932 -H 280 -Fill "#FFFFFF" -Stroke "#8EBDB7"
Draw-CardTitle -Text "EVIDENCE-ONLY PROMPT" -X ($outX + 28) -Y 410 -Color "#19776F"
Draw-Lines -Lines @(
    "Question + numbered authorized passages",
    "[1] … [k].",
    "Documents are untrusted evidence, not instructions.",
    "Claims must be supported by supplied evidence."
) -X ($outX + 28) -Y 468 -Font $fontBody -LineGap 48

Draw-Arrow -X1 ($x3 + 498) -Y1 665 -X2 ($x3 + 498) -Y2 710 -Color "#168477" -StrokeWidth 6
Draw-Card -X $outX -Y 720 -W 932 -H 230 -Fill "#EAF6F4" -Stroke "#80B8B0"
Draw-CardTitle -Text "LOCAL GENERATION" -X ($outX + 28) -Y 746 -Color "#19776F"
Draw-Lines -Lines @(
    "Ollama · mistral:latest",
    "Generates a draft from the authorized context.",
    "No external LLM call in this workflow."
) -X ($outX + 28) -Y 804 -Font $fontBody -LineGap 48

Draw-Arrow -X1 ($x3 + 498) -Y1 950 -X2 ($x3 + 498) -Y2 990 -Color "#168477" -StrokeWidth 6
Draw-Card -X $outX -Y 1000 -W 932 -H 285 -Fill "#FFFFFF" -Stroke "#8EBDB7"
Draw-CardTitle -Text "CITATION VALIDATION" -X ($outX + 28) -Y 1025 -Color "#19776F"
Draw-Lines -Lines @(
    "Each label must resolve to authorized evidence.",
    "Unknown labels or no valid citation cause abstention.",
    "Incomplete answers are also rejected.",
    "Checks citation existence and scope, not entailment."
) -X ($outX + 28) -Y 1083 -Font $fontBody -LineGap 47

Draw-Arrow -X1 ($x3 + 498) -Y1 1285 -X2 ($x3 + 498) -Y2 1325 -Color "#168477" -StrokeWidth 6
Draw-Card -X $outX -Y 1335 -W 932 -H 270 -Fill "#EEF8F3" -Stroke "#78AE91"
Draw-CardTitle -Text "EXAMPLE OUTPUT · FICTIONAL DEMO" -X ($outX + 28) -Y 1357 -Color "#23694A"
Draw-Lines -Lines @(
    "…deadline was March 15, 2025 [1][5].",
    "…no replacements by March 20, 2025 [3].",
    "Source: demo_contract_evidence.docx, paras. 4, 5, 7."
) -X ($outX + 28) -Y 1409 -Font $fontExample -LineGap 43 -Color "#183247"

# Indexing foundation
Draw-Card -X 75 -Y 1700 -W 3150 -H 260 -Fill "#F1F4F7" -Stroke "#CCD8E3" -Radius 28 -StrokeWidth 3
Draw-Text -Text "LOCAL DOCUMENT INDEX  ·  built during ingestion" -X 108 -Y 1720 -Font $fontCard -Color "#183247"

$stepY = 1780
$stepH = 100
$stepW = 660
$stepXs = @(105, 870, 1635, 2400)
$stepFills = @("#FFFFFF", "#FFFFFF", "#FFFFFF", "#EAF6F4")
$stepStrokes = @("#B9C9D8", "#B9C9D8", "#B9C9D8", "#80B8B0")
$stepTexts = @(
    "PDF / DOCX",
    "Extract text + retain page / paragraph",
    "Chunk text + attach matter metadata",
    "SQLite FTS5 + 384-D local vectors"
)
for ($i = 0; $i -lt $stepXs.Count; $i++) {
    Draw-Card -X $stepXs[$i] -Y $stepY -W $stepW -H $stepH -Fill $stepFills[$i] -Stroke $stepStrokes[$i] -Radius 18 -StrokeWidth 2
    Draw-Text -Text $stepTexts[$i] -X ($stepXs[$i] + 20) -Y ($stepY + 31) -Font $fontSmall -Color "#263F53"
}
Draw-Arrow -X1 773 -Y1 1830 -X2 853 -Y2 1830 -Color "#71879A" -StrokeWidth 5
Draw-Arrow -X1 1538 -Y1 1830 -X2 1618 -Y2 1830 -Color "#71879A" -StrokeWidth 5
Draw-Arrow -X1 2303 -Y1 1830 -X2 2383 -Y2 1830 -Color "#71879A" -StrokeWidth 5
Draw-Text -Text "Private matter IDs remain attached to chunks; public sources use the separate public tier." -X 108 -Y 1894 -Font $fontSmall -Color "#52697C"

# Figure note
Draw-Text -Text "Figure 1. Query processing in the current prototype. FTS5 performs lexical token matching; dense search uses deterministic hash embeddings. The example answer uses fictional demo data." -X 78 -Y 1980 -Font $fontSmall -Color "#52697C"

$bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
Write-Output "Created $outputPath"
