// 各種プラグインのロード
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const UglifyJsPlugin = require("uglifyjs-webpack-plugin");
const AutoPrefixer = require("autoprefixer");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const OptimizeCSSAssetsPlugin = require("optimize-css-assets-webpack-plugin");
const TerserJSPlugin = require("terser-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const globule = require("globule");

// 環境名
// const ENV = "production";
const ENV = "development";
// ソースマップを生成するかどうか
const USE_SOURCE_MAP = (ENV === "development");
// ビルド先パス
const DEST_PATH = path.join(__dirname, "./public");

// エントリーポイントに含めるパターン
const ejsTargetTypes = {ejs: "html"};
const getEntriesList = (targetTypes) => {
  const entriesList = {};
  for (const [srcType, targetType] of Object.entries(targetTypes)) {
    const filesMatched = globule.find([`**/*.${srcType}`, `!**/_*.${srcType}`], {cwd : `${__dirname}/src`});

    for (const srcName of filesMatched) {
      const targetName = srcName.replace(new RegExp(`.${srcType}$`, 'i'), `.${targetType}`);
      entriesList[targetName] = `${__dirname}/src/${srcName}`;
    }
  }
  return entriesList;
}

const app = {
  mode: ENV,
  devtool: (ENV === "development") ? "source-map" : false,
  entry: Object.assign(
    {
      app: [
        "./src/js/main.js",
        "./src/scss/style.scss",
      ],
    },
    getEntriesList(ejsTargetTypes)
  ),
  output: {
    path: path.resolve(__dirname, DEST_PATH),
    filename: "js/[name].min.js",
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
        test: /\.ejs$/,
        use: [
          "html-loader",
          "ejs-html-loader",
        ]
      },
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
  resolve: {
    extensions: [".js"],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "css/style.min.css",
    }),
    new CopyWebpackPlugin(
      [
        {
          from: "**/*",
          to: "img",
        },
      ],
      {
        context: "src/img",
      },
    ),
  ],
  optimization: {
    minimizer: [
      new TerserJSPlugin({}),
      new OptimizeCSSAssetsPlugin({}),
      new UglifyJsPlugin(),
    ]
  },
  performance: {
    hints: false,
  },
};

// EJSの変換定義を現在存在するファイル分だけ自動的に追加
for (const [targetName, srcName] of Object.entries(getEntriesList({ejs: "html"}))) {
  app.plugins.push(new HtmlWebpackPlugin({
    filename : targetName,
    template : srcName,
  }));
}

module.exports = [app];
