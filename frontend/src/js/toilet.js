// ###################################################################
//    トイレチェッカー
// ###################################################################
import * as palette from 'google-palette';
const $ = require('../../node_modules/jquery/dist/jquery.min.js');
const Common = require('./common.js');
const Chart = require('../../node_modules/chart.js/dist/Chart.bundle.js');
const dateformat = require('dateformat');
const API = require('./call-api-toilet.js');

/**
 * 前回取得した現況情報 (キャッシュ用)
 */
let previousFetchedStatusCache;

// Chart.js グローバル設定
Chart.defaults.global.defaultFontFamily =
  '"Noto Sans JP", "Hiragino Kaku Gothic ProN", "ヒラギノ角ゴ ProN W3", Meiryo, メイリオ, sans-serif';

$(() => {
  const pageID = $('body').attr('id');
  const suffix = /^page-(.*)$/g.exec(pageID)[1];

  if (suffix === 'toilet' && 0 < $('.js-dashboard').length) {
    // ダッシュボード用: 自動で現況取得
    fetchCurrentStatus(true);
  }
});

/**
 * ダッシュボード: 現況を画面に反映
 *
 * @param {boolean} isLoop 完了後に再度時間を置いて取得を行うようにするかどうか
 */
export const fetchCurrentStatus = (isLoop) => {
  API.apiRules.fetchCurrentStatus.call({
    loadingSpinner: false,
    success: json => {
      Common.toggleValidMode(true);

      if (JSON.stringify(json) === previousFetchedStatusCache) {
        console.info('取得した現況情報が前回の結果と合致しているため画面更新をスキップします。');
        return;
      }

      // 今回の現況情報を保管
      previousFetchedStatusCache = JSON.stringify(json);

      // 画面変更を行っていることを表すために一時的にローディングスピナーを出す
      Common.viewLoadingSpinner(true);

      // 一定時間経過後に画面更新
      setTimeout(() => {
        Common.viewLoadingSpinner(false);

        // 既存の現況をすべてクリア
        $('.js-status-item:not(.js-status-item-template)').remove();

        if (json.success === false) {
          // 取得できなかったときはエラー内容を出力する
          Common.toggleValidMode(false);
          throw new Error(`${json.message}`);
        }

        let counter = -1;
        for (const item of json.status) {
          counter++;

          const $newItem = $('.js-status-item-template')
            .clone()
            .removeClass('js-status-item-template d-none');

          if (item.valid === true) {
            $newItem.find('.js-status-invalid').remove();

            $newItem.find('.js-status-valid-collapse').attr('href', `#js-toilet-group-${counter}`);

            $newItem.find('.js-status-valid').addClass(
              item.name.includes('男') ? 'callout-primary' : 'callout-danger'
            );
            $newItem.find('.js-status-name').text(item.name);
            $newItem.find('.js-status-rate').text(item.rate100);
            $newItem.find('.js-status-progressbar')
              .attr('aria-valuenow', item.used)
              .attr('aria-valuemax', item.max)
              .css('width', `${item.rate100}%`)
              .addClass(
                (100 <= item.rate100) ? 'bg-danger'
                  : (50 <= item.rate100) ? 'bg-warning'
                    : 'bg-success'
              );
            const availableCount = item.max - item.used;
            if (0 < availableCount) {
              $newItem.find('.js-status-available').text(availableCount);
            } else {
              $newItem.find('.js-status-available').text('');
              $newItem.find('.js-status-available-unit').text('無し');
            }

            // トイレグループに属するトイレごとの仔細
            if (0 < item.details.length) {
              $newItem.find('.js-toilet-group-details').attr('id', `js-toilet-group-${counter}`);
              const $details = $newItem.find('.js-toilet-group-details .js-toilet-group-details-container');
              $details.empty();

              let subCounter = -1;
              for (const subItem of item.details) {
                subCounter++;

                // 状態テキストの決定
                let subStatus = '';
                if (subItem.valid) {
                  subStatus = subItem.used ? '使用中' : '空き';
                } else {
                  subStatus = '使用不能';
                }

                // 仔細要素を追加
                $details.append(
                  $('<dl />')
                    .append(
                      $('<dt />').text(subItem.name)
                    )
                    .append(
                      $('<dd />')
                        .text(subStatus)
                        .addClass('my-0')
                    ).addClass(
                      // 末尾に下余白を付けない
                      (item.details.length <= subCounter + 1) ? 'mb-0' : ''
                    )
                );
              }
            } else {
              $newItem.find('.js-toilet-group-details').remove();
            }
          } else {
            $newItem.find('.js-status-valid-collapse').remove();
            $newItem.find('.js-status-invalid').addClass(
              item.name.includes('男') ? 'callout-primary' : 'callout-danger'
            );
            $newItem.find('.js-status-name').text(item.name);
          }

          // 要素追加
          $('.js-dashboard-valid').append($newItem);
        }
      }, 250);
    },
    fail: e => {
      Common.toggleValidMode(false);
    },
    final: () => {
      if (isLoop) {
        // 定期的に現況を取得
        setTimeout(() => fetchCurrentStatus(true), 5000);
      }
    }
  });
};

/**
 * ログ: ログを画面に反映
 */
export const fetchLogs = () => {
  // APIパラメーターをセット
  const beginDate = new Date();
  const endDate = new Date(beginDate.getTime());
  const beginHoursPerDay = 9;
  const endHoursPerDay = 19;
  const format = 'yyyymmdd';
  const stepHours = 1;
  beginDate.setDate(endDate.getDate() - 7);
  API.apiRules.fetchLogs.urlSuffix =
    `?begin_date=${dateformat(beginDate, format)}&end_date=${dateformat(endDate, format)}&` +
    `begin_hours_per_day=${beginHoursPerDay}&end_hours_per_day=${endHoursPerDay}&step_hours=${stepHours}`;

  API.apiRules.fetchLogs.call({
    success: json => {
      $('.js-logboard-invalid').hide();
      $('.js-logboard-valid').show();
      $('.js-logboard-container').addClass('flex-fill');

      // 既存の現況をすべてクリア
      $('.js-logboard-canvas:not(.js-logboard-canvas-template)').remove();

      if (json.success === false) {
        // 取得できなかったときはエラー内容を出力する
        throw new Error(`${json.message}`);
      }

      // 出力グラフ情報
      const graphs = json.graphs;

      // 系列色を生成
      const colors = palette('mpn65', graphs.length).map(hex => `#${hex}`);

      // 系列分だけグラフを生成
      graphs.forEach((item, index) => {
        // テンプレート要素からキャンバスをコピー
        const $newItem = $('.js-logboard-canvas-template')
          .clone()
          .removeClass('js-logboard-canvas-template d-none');
        if (index === 0) {
          $newItem.addClass('mb-5');
        } else if (index + 1 <= graphs.length) {
          $newItem.addClass('mt-5');
        } else {
          $newItem.addClass('my-5');
        }

        item.data.datasets[0] = Object.assign(item.data.datasets[0], {
          backgroundColor: `${colors[index]}66`,
          hoverBackgroundColor: `${colors[index]}ff`,
          borderColor: `${colors[index]}aa`,
          borderWidth: 1,
          animation: true
        });
        item.options = {
          title: {
            // グラフタイトル表示
            display: true,
            fontSize: 28,
            text: item.data.datasets[0].label
          },
          legend: {
            // 凡例非表示
            display: false
          },
          scales: {
            yAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                fontSize: 18,
                labelString: '使用回数'
              },
              ticks: {
                beginAtZero: true,
                userCallback: (label, index, labels) => {
                  if (Math.floor(label) === label) {
                    return label;
                  }
                }
              }
            }]
          }
        };
        new Chart($newItem, item);

        // 画面上に追加
        $('.js-logboard-canvas-wrapper').append($newItem);
      });
    },
    fail: e => {
      $('.js-logboard-invalid').show();
      $('.js-logboard-valid').hide();
      $('.js-logboard-container').removeClass('flex-fill');
    }
  });
};
