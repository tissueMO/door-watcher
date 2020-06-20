// 各種プラグインのロード
const merge = require("webpack-merge");
const common = require("./webpack.common.js");


// 開発用サーバーの設定追加分
module.exports = merge(common.app, {
  mode: "development",
  devtool: "source-map",
  devServer: {
    contentBase: common.DEST_PATH,
    watchContentBase: true,
    port: 3000,
    open: true,
  },
})
