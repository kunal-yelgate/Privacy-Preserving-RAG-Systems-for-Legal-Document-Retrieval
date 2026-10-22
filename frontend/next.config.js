/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Offline-first: disable remote image optimization
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
