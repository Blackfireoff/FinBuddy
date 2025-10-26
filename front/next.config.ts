import type { NextConfig } from "next";

const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  distDir: 'build',
};
export default nextConfig;
