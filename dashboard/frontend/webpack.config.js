// 各種プラグインのロード
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const UglifyJsPlugin = require("uglifyjs-webpack-plugin");
const AutoPrefixer = require("autoprefixer");

// 環境名
const ENV = "development";
// ソースマップを生成するかどうか
const USE_SOURCE_MAP = (ENV === "development");
// ビルド先パス
const DEST_PATH = "./public";


module.exports = [
  {
    mode: ENV,
    devtool: (ENV === "development") ? "source-map" : false,
    entry: {
      app: [
        "./src/js/main.js",
        "./src/scss/style.scss",
      ],
    },
    output: {
      path: path.resolve(__dirname, DEST_PATH),
      filename: "js/[name].js",
      publicPath: "/",
    },
    devServer: {
      contentBase: DEST_PATH,
      watchContentBase: true,
      port: 3000,
      open: true,
    },
    module: {
      rules: [
        {
          test: /\.js?$/,
          exclude: /node_modules/,
          loader: "babel-loader",
        },
        {
          test: /\.scss$/,
          use: [{
            loader: MiniCssExtractPlugin.loader,
          }, {
            loader: "css-loader",
            options: {
              sourceMap: (ENV === "development") ? USE_SOURCE_MAP : false,
            },
          }, {
            loader: "postcss-loader",
            options: {
              plugins: [
                AutoPrefixer(),
              ],
            },
          }, {
            loader: "sass-loader",
            options: {
              sourceMap: (ENV === "development") ? USE_SOURCE_MAP : false,
            },
          }],
        },
        {
          test: /\.js$/,
          exclude: /node_modules/,
          enforce: 'pre',
          use: [
            {
              loader: 'eslint-loader',
            },
          ]
        },
      ],
    },
    optimization: {
      minimizer: [
        new UglifyJsPlugin(),
      ],
    },
    resolve: {
      extensions: [".js"],
    },
    plugins: [
      new MiniCssExtractPlugin({
        filename: "css/style.css",
      }),
    ],
  },
];
