トイレ在室監視ソリューション
====

## Summary

遠隔地から個室トイレが使用中であるかどうかをリアルタイムで確認できるようにするソリューションです。  
空室時にドアが開くタイプの個室トイレにのみ使用することができます。  
// もちろんトイレに限らず、使用中にのみドアが閉まるような設備であれば使用することができます。  


## Description

### アーキテクチャー全体図

![Architecture](https://user-images.githubusercontent.com/20965271/72682494-dc507f80-3b10-11ea-9513-dbce75efe9bf.png)

#### センサー部 [sensor]

単体で Wi-Fi モジュールが付いている ESPr Door Sensor を使用します。  
Arduino IDE を用いてソースコードをコンパイルして書き込みます。  

コンパイルに必要な `/sensor/settings.h` は環境依存するためバージョン管理に含めていませんが、環境に応じて以下のマクロを定義したファイルとして配置しておく必要があります。  

- `#define SSID {SSID}`
- `#define PASSWORD {PASSWORD}`
- `#define HOSTNAME {HOSTNAME}`
- `#define PORT {PORT}`

リードスイッチに磁石が接近した瞬間、および磁石が離れた瞬間に所定の Wi-Fi アクセスポイントに接続を行い、インターネットを介して (宛先アドレスによってはLAN内で完結することも可能です) サーバーにPOSTします。  


#### サーバー部 [server]

Apache2 + mod_wsgi を利用して Python の Flask で動かします。  
ただし `/server/Dockerfile` を用いてイメージをビルドし、Docker環境上で動かします。  


#### フロント部 [front]

Webサーバーは特に想定していませんが、コンテンツのビルドには Node.js v12 以降が必要です。  
ビルドして生成されたファイルは、Webサーバーの公開ディレクトリーに配置します。  


### ユースケース

- 個室トイレに人が入る (=ドアが閉まった状態が継続する)
    - [sensor] サーバーにドアが閉まったことを送信
    - [server] サーバーが所定のドアが閉まったことをDBに保存
- 個室トイレから人が出る (=ドアが開いた状態が継続する)
    - [sensor] サーバーにドアが開いたことを送信
    - [server] サーバーが所定のドアが開いたことをDBに保存
- 個室トイレの空き状況を確認したい
    - [front] スマホやPCからダッシュボードを開く
    - [front] 現在の使用率、空き状況を確認できる
- サーバーとしての機能を停止/再開させたい
    - [front] スマホやPCから管理者用ダッシュボードを開く
    - [front] サーバーの機能停止/再開を行える


## Dependency

#### センサー部 [sensor]

- Arduino IDE
- ESPr Door Sensor
- FTDI USBシリアル変換アダプター
    - ESPr Door Sensor にプログラムを書き込むのに必要


#### サーバー部 [server]

いずれもDockerfileにて定義があるため、ビルドしたDockerイメージを用いるだけであれば手動でインストールする必要はありません。  

- Docker
- Python 3.7
    - Python パッケージ
        - Flask
        - alembic
        - SQLAlchemy
        - その他については `/server/requirements.txt` を参照
- Apache2
    - mod_wsgi 4.5


#### フロント部 [front]

- Node.js 12+
- Yarn
- Nodes.js パッケージ
    - Webpack
    - Babel
    - Chart.js
    - Sass
    - EJS
    - ESLint
    - その他については `/front/package.json` を参照


## Setup

本リポジトリーから Clone してから実際に動かすまでの手順を示します。  


### センサー部 [sensor]

- ESPr Door Sensor への給電、および、これと接続した FTDI USBシリアル変換アダプター をPCにUSB接続します。
    - ESPr Door Sensor のジャンパーソケットは [PROG] 側に接続しておきます。
    - FTDI USBシリアル変換アダプター のジャンパーソケットは [3.3V] 側に接続しておきます。
    - バイナリーの書き込みにあたっては ESP8266 固有の設定が必要となります。詳しくはスイッチサイエンス社 Wiki (公式) を参照。
        - http://trac.switch-science.com/wiki/ESP-DOOR
- Arduino IDE から `/sensor/ESPrDoorSensor.ino` を開きます。
- `/sensor/settings.h` を作成し、環境依存する値のマクロを定義します。
    - `#define SSID {SSID}`
    - `#define PASSWORD {PASSWORD}`
    - `#define HOSTNAME {HOSTNAME}`
    - `#define PORT {PORT}`
- コンパイル & ESPr Door Sensor への書き込みを行います。


### サーバー部 [server]

- コマンドライン上で `/server` に移動した状態で以下のコマンドでDockerイメージのビルドを実行します。
    - `$ docker build -t {TAG_NAME} .`
- ビルドに失敗した場合、適宜Dockerfileを修正して下さい。
- ビルドが終わったら以下のコマンドでコンテナーを起動します。
    - `$ docker run -p 80:80 --rm -d {TAG_NAME}`


### フロント部 [front]

- コマンドライン上で `/frontend` に移動した状態で以下のコマンドで Node.js で使用する依存パッケージをインストールします。
    - `$ yarn`
- `/frontend/src/js/settings.js` を作成し、環境依存する値 (APIサーバーのURL、末尾に / を含まないもの) を定義します。
    - `export const apiServerURLBase = 'http://HOSTNAME';`
- 以下のコマンドで公開ファイル群をビルドします。
    - `$ yarn run webpack`
        - 開発モードは `/frontend/webpack.config.js` のENV を `"development"` とします。
        - 本番モードは `/frontend/webpack.config.js` のENV を `"production"` とします。
- `/frontend/public/` 以下に作られたファイルを、任意のWebサーバーの公開ディレクトリーに配置します。
    - アーキテクチャー全体図では Web Server に相当します。


## Usage

### センサー部 [sensor]

(Setup/センサー部 [sensor] での工程が完了している前提とします)

- ESPr Door Sensor のジャンパーソケットを [RUN] 側に接続します。
    - Arduino IDE のシリアルモニターを使用する場合は FTDI USBシリアル変換アダプター は接続したままにしておく必要があります。
- ESPr Door Sensor のリードスイッチに磁石を接近させます。
    - シリアルモニターを使用すると、Wi-Fiに接続を行い `[ Closed ]` として表示されるところまでのログが確認できます。
- ESPr Door Sensor のリードスイッチから磁石を離します。
    - シリアルモニターを使用すると、Wi-Fiに接続を行い `[ Opened ]` として表示されるところまでのログが確認できます。
- 実運用においては、ESPr Door Sensor をトイレの壁面や上枠等動かない箇所に取り付け、磁石を可動部かつドアを閉じた際に ESPr Door Sensor に接する箇所に取り付けます。


### サーバー部 [server]

(Setup/サーバー部 [server] での工程が完了している前提とします)

- サーバーに疎通できるクライアント環境のブラウザーから以下のURLにアクセスします。
    - `http://{DOMAIN_NAME}/health`
        - これはヘルスチェック用のAPIです。
- 画面上に `{}` とだけ表示されれば正常に起動できています。

- サーバーログを確認するには、以下のコマンドからDockerコンテナー内に入ります。
    - `$ docker ps`
        - 起動中のコンテナーの CONTAINER ID を確認します。
    - `$ docker exec -it {CONTAINER_ID} bash`
    - `# tail -f /var/log/apache2/access.log`
        - クライアントがアクセスしてきたURLとステータスコードを確認できます。
    - `# tail -f /var/log/apache2/error.log`
        - サーバーアプリケーション内でエラー発生した際のスタックトレースやアプリケーションが吐き出したログを確認できます。


### フロント部 [front]

(Usage/センサー部 [server]、Usage/サーバー部 [server]、Setup/フロント部 [front] での工程が完了している前提とします)

- ビルドしたフロント用コンテンツを配置しているWebサーバーに疎通できるクライアント環境のブラウザーから、フロント用コンテンツの index.html にアクセスします。
    - ダッシュボードの画面が表示されます。
    - センサー部のリードスイッチに磁石を近づけたり、離したりすると、ダッシュボードの表示が5秒置きに更新されます。
    - 非最新のブラウザーや Internet Explorer 等では正しく動作しない可能性があります。


## Reference

- [ESPr Door Seonsor の使い方 - スイッチサイエンス](http://trac.switch-science.com/wiki/ESP-DOOR)
- [craicerjack/apache-flask](https://hub.docker.com/r/craicerjack/apache-flask/)
- [ndegardin/apache-wsgi](https://hub.docker.com/r/ndegardin/apache-wsgi)


## License

[MIT](LICENSE.md)


## Author

[tissueMO](https://github.com/tissueMO)
