const path = require("path");
const merge = require('webpack-merge');
const common = require('./webpack.common.js');
// ビルド先パス
const DEST_PATH = path.join(__dirname, "./public");

module.exports = merge(common[0], {
    mode: 'development',
    devtool: 'source-map',        
    devServer: {
        contentBase: DEST_PATH,
        watchContentBase: true,
        port: 3000,
        open: true,
    },
})