/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // strict mode double-renders, costs perf in dev
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
  // Optimize JS bundle sizes
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  // Faster page transitions: prefetch aggressively
  experimental: {
    optimisticClientCache: true,
    // Turbo mode (Next.js 14 dev speed improvement)
    turbo: {},
  },
};

module.exports = nextConfig;
