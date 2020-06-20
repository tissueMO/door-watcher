// 各種プラグインのロード
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const AutoPrefixer = require("autoprefixer");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const globule = require("globule");

// ビルド先パス
const DEST_PATH = path.join(__dirname, "./public");

// エントリーポイントに含めるパターン
const getEntriesList = (targetTypes) => {
  const entriesList = {};
  for (const [srcType, targetType] of Object.entries(targetTypes)) {
    const filesMatched = globule.find([`**/*.${srcType}`, `!**/_*.${srcType}`], {cwd : `${__dirname}/src`});

    for (const srcName of filesMatched) {
      const targetName = srcName.replace(new RegExp(`.${srcType}$`, "i"), `.${targetType}`);
      entriesList[targetName] = `${__dirname}/src/${srcName}`;
    }
  }
  return entriesList;
}

const app = {
  entry: Object.assign(
    {
      app: [
        "./src/js/main.js",
        "./src/scss/style.scss",
      ],
    },
  ),
  output: {
    path: path.resolve(__dirname, DEST_PATH),
    filename: "js/[name].min.js",
    publicPath: "/",
  },
  module: {
    rules: [
      {
        test: /\.ejs$/,
        use: [
          { loader: "html-loader" },
          { loader: "ejs-html-loader" },
        ],
      },
      {
        test: /\.js?$/,
        exclude: /node_modules/,
        loader: "babel-loader",
      },
      {
        test: /\.scss$/,
        use: [
          { loader: MiniCssExtractPlugin.loader },
          { loader: "css-loader" },
          {
            loader: "postcss-loader",
            options: {
              plugins: [
                AutoPrefixer(),
              ],
            },
          },
          { loader: "sass-loader" },
        ],
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        enforce: "pre",
        use: [
          { loader: "eslint-loader" },
        ],
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

module.exports = {
  DEST_PATH: DEST_PATH,
  app: app,
};
