const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common[0], {
    mode: 'production',
    devtool: false,
});