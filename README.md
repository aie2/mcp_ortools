# OR MCP Server

`lp_mcp_server.py` は `calc_lp.py` の線形計画ソルバーを参考にして mcp サーバー化したものです。 `solve_linear_program` 関数経由で OR-Tools の結果を返します。

## CLI 設定

1. Codex CLI から依存関係のインストールやサーバー起動を行うため、該当リポジトリを CLI で開きます。
2. CLI 側の MCP 設定メニュー（`codex config mcp add` など）で、このプロジェクトを MCP サーバーとして登録します。これにより CLI が `lp_mcp_server.py` を起動し、`solve_linear_program` ツールを利用できるようになります。

## CLI からの命令方法

1. Codex CLI に「`example.txt` を読み、その内容で mcp の `ortools-lp` を実行してください」と指示します。Codex はファイル内容を解析し、変数の下限制約・目的関数の向きと係数・制約行を JSON にまとめてツールへ送信します。`example.txt` のフォーマットは特に固定していないため、CLI 側が解析できる形であれば自由に記述できます。
2. MCP サーバーは OR-Tools で最適化を解き、ステータス・目的関数値・変数値・双対情報を CLI 上に返します。`example.txt` を書き換えれば別の線形計画も同じ流れで解かせることができます。
