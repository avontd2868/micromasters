var webpack = require('webpack');
var path = require("path");
var BundleTracker = require('webpack-bundle-tracker');
const { config, babelSharedLoader } = require(path.resolve("./webpack.config.shared.js"));

const prodBabelConfig = Object.assign({}, babelSharedLoader);

prodBabelConfig.query.plugins.push(
  "transform-react-constant-elements",
  "transform-react-inline-elements"
);

const prodConfig = Object.assign({}, config);
prodConfig.module.loaders = [prodBabelConfig, ...config.module.loaders];

module.exports = Object.assign(prodConfig, {
  context: __dirname,
  output: {
    path: path.resolve('./static/bundles/'),
    filename: "[name]-[chunkhash].js"
  },

  plugins: [
    new webpack.DefinePlugin({
      'process.env': {
        'NODE_ENV': '"production"'
      }
    }),
    new webpack.optimize.UglifyJsPlugin({
      compress: {
        warnings: false
      },
      sourceMap: true,
    }),
    new webpack.optimize.CommonsChunkPlugin({
      name: 'common',
      minChunks: 2,
    }),
    new BundleTracker({
      filename: './webpack-stats.json'
    }),
    new webpack.LoaderOptionsPlugin({
      minimize: true
    })
  ],
  devtool: 'source-map'
});
