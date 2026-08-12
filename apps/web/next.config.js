/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  webpack: (config) => {
    // pdfjs pulls optional node canvas; browser builds must stub it.
    config.resolve.alias = {
      ...config.resolve.alias,
      canvas: false,
    };
    return config;
  },
};

module.exports = nextConfig;
