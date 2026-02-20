# OR MCP Server

`lp_mcp_server.py` は `calc_lp.py` の線形計画ソルバーを参考にして mcp サーバー化したものです。 `solve_linear_program` 関数経由で OR-Tools の結果を返します。

## Python 依存関係のインストール

Python 3.10 以降を用意し、仮想環境を作成してから OR-Tools と MCP サーバー実装で必要なライブラリをインストールします。

```
pip install ortools mcp typing_extensions
```

## CLI 設定

CLI 側の MCP 設定メニュー（codex ならば `codex mcp add` など）で、このプロジェクトを MCP サーバーとして登録します。これにより CLI が `lp_mcp_server.py` を起動し、最適化ツールを利用できるようになります。

## CLI からの命令方法

1. CLI に「`example.txt` を読み、その内容で mcp の `ortools-lp` を実行してください」と指示します。CLI(実際はその先の AI) はファイル内容を解析し、変数の下限制約・目的関数の向きと係数・制約行を JSON にまとめてツールへ送信します。`example.txt` のフォーマットは特に固定していないため、CLI 側が解析できる形であれば自由に記述できます。
2. MCP サーバーは OR-Tools で最適化を解き、ステータス・目的関数値・変数値・双対情報を CLI 上に返します。`example.txt` を書き換えれば別の線形計画も同じ流れで解かせることができます。
