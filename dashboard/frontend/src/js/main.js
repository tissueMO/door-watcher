import '../../node_modules/popper.js/dist/umd/popper.min.js';
import '../../node_modules/bootstrap/dist/js/bootstrap.min.js';
import '../../node_modules/@coreui/coreui/dist/js/coreui.min.js';
import * as palette from 'google-palette';
const $ = require('../../node_modules/jquery/dist/jquery.min.js');
const Chart = require('../../node_modules/chart.js/dist/Chart.bundle.js');
const API = require('./call-api.js');
const Common = require('./common.js');

$(() => {
  if (0 < $('.js-dashboard')) {
    // ダッシュボード用: 自動で現況取得
    fetchCurrentStatus();
  }

  if (0 < $('.js-log')) {
    // ログページ用: 自動でログ取得
    fetchLogs();

    // 再取得ボタン
    $('.js-fetch-logs').on('click', () => {
      fetchLogs();
    });
  }

  // サイドメニュー用: 緊急停止 or 再開
  $('.js-action-emergency').on('click', () => {
    API.apiRules.emergency({
      success: json => {
        Common.toggleValidMode(json.valid === true);
        alert(`モード [${json.action}] への移行に成功しました。`);
      },
      fail: e => alert('モードの移行に失敗しました。詳細はエラーログをご覧下さい。')
    });
  });
});

/**
 * ダッシュボード: 現況を画面に反映
 */
const fetchCurrentStatus = () => {
  API.apiRules.fetchCurrentStatus({
    success: json => {
      Common.toggleValidMode(true);

      for (const item of json.status) {
        const $newItem = $('.js-dashboard-item-template')
          .clone()
          .removeClass('js-dashboard-item-template d-none');

        if (item.invalid !== true) {
          $newItem.find('.js-status-invalid').remove();
          $newItem.find('.js-status-name').text(item.name);
          $newItem.find('.js-status-rate').text(item.rate100);
          $newItem.find('.js-status-progressbar')
            .attr('aria-valuenow', item.current)
            .attr('aria-valuemax', item.max)
            .css('width', `${item.rate100}%`)
            .addClass(
              (100 <= item.rate100) ? 'bg-danger'
                : (50 <= item.rate100) ? 'bg-warning'
                  : 'bg-success'
            );
          $newItem.find('js-status-available').text(item.max - item.current);
        } else {
          $newItem.find('.js-status-valid').remove();
          $newItem.find('.js-status-name').text(item.name);
        }

        // 要素追加
        $('.js-dashboard-valid').append($newItem);
      }
    },
    fail: e => {
      Common.toggleValidMode(false);
    },
    final: () => {
      // 定期的に現況を取得
      setTimeout(fetchCurrentStatus, 5000);
    }
  });
};

/**
 * ログ: ログを画面に反映
 */
const fetchLogs = () => {
  API.apiRules.fetchLogs({
    success: json => {
      const ctx = $('.js-logboard-canvas');
      // 色を生成
      const colors = palette('mpn65', json.datasets.length).map(hex => `#${hex}`);
      const datasets = json.datasets.map((value, i) => {
        return {
          label: value.label,
          data: value.data,
          backgroundColor: 'rgba(0, 0, 0, 0)',
          borderColor: colors[i],
          pointRadius: 3,
          pointHitRadius: 6
        };
      });
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: json.labels,
          datasets: datasets
        },
        options: {
          title: {
            display: true,
            text: 'トイレ入退室ログ'
          }
        }
      });
    }
  });
};
