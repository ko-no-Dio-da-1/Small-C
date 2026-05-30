# Small-C 互動式解譯器 (Interactive Interpreter & REPL)

本專案實作了一個完整支援 **Small-C 語言** 規格的互動式解譯器與整合式 REPL 開發環境，採用 Python 3 撰寫，無需額外安裝第三方套件。

## 系統架構與模組設計

本專案完全遵循模組化設計（Modular Design），將直譯器的各個生命週期職責明確切分：

1.  **`main.py` (主程式入口)**
    *   負責啟動系統。若從命令列傳入檔案路徑（如 `python main.py script.sc`），則會以批次模式（Batch Mode）直接載入、語法檢查並執行該指令檔；否則進入互動式 REPL 介面。
2.  **`repl.py` (整合互動環境)**
    *   實作程式碼編輯緩衝區與命令列。
    *   管理環境與編輯指令（如 `APPEND`、`INSERT`、`DELETE`、`EDIT`、`LIST`、`LOAD`、`SAVE`、`NEW`）。
    *   管理執行控制指令（如 `RUN`、`CHECK`、`TRACE`、`VARS`、`FUNCS`）。
    *   實作**直接執行模式**：當輸入不屬於 REPL 指令且非函式定義時，即時編譯並於當前全域環境執行。
3.  **`lexer.py` (詞法分析與前處理)**
    *   過濾註解（`/* ... */` 及 `// ...`），並保留換行符以確保錯誤回報行號的精確性。
    *   處理 `#define NAME VALUE` 常數巨集替換。
    *   將源碼字串切割為各種類別的 Token（識別碼、關鍵字、十進位與十六進位整數、字元常數、字串常數、雙字元與單字元運算子）。
4.  **`parser.py` (語法分析器)**
    *   實作遞迴下降（Recursive Descent）語法分析，並使用 **Pratt 優先權爬升法** 解析 13 級優先級的 Small-C 表達式。
    *   建構完整的抽象語法樹（AST）。
    *   提供精準的語法錯誤定位與偵錯提示（包含出錯的行號與欄位）。
5.  **`interpreter.py` (語意分析與執行引擎)**
    *   以 Tree-walking 方式遍歷 AST 節點執行。
    *   處理函式呼叫的壓棧（Stack Frame）與彈棧，支援區域變數生命週期與遞迴呼叫。
    *   控制單步執行追蹤（`TRACE ON/OFF`）。
    *   執行期錯誤處理機制（包含除以零、陣列越界、空指標檢驗），防止直譯器崩潰。
6.  **`symtable.py` (作用域與符號表)**
    *   管理變數與函式的符號資訊（變數型別、虛擬地址、陣列維度、函式簽名等）。
    *   支援巢狀作用域（Scope），在進入函式或區塊時動態繼承/切換。
7.  **`memory.py` (虛擬記憶體管理器)**
    *   模擬實體 C 語言記憶體配置（區分全域變數區、呼叫堆疊區、堆積區）。
    *   分配虛擬記憶體地址（例如全域區 `1000+`，堆疊區 `100000+`），變數與陣列存取皆透過虛擬地址間接定址。
    *   這使我們能實作真正的**指標取址 `&` 與取值 `*`** 以及 **陣列變數衰退為指標（Pointer Decay）**。
    *   在讀寫記憶體時，會主動比對分配區間，達成**執行期陣列越界安全偵測**與**空指標存取安全偵測**。
8.  **`builtins.py` (內建函式庫)**
    *   實作 C 標準庫與作業規定的內建函式，包含 I/O (`printf`, `scanf`, `putchar` 等)、字串操作 (`strlen`, `strcmp` 等)、數學 (`sqrt`, `pow`, `rand`, `srand` 等) 與記憶體操作 (`memset`, `sizeof_int` 等)。

---

## 互動環境環境指令 (REPL Commands)

啟動解譯器後，在 `sc>` 提示符下可輸入以下指令：

| 指令 | 說明 | 範例 |
| :--- | :--- | :--- |
| **`LOAD <file>`** | 自指定檔案載入 Small-C 原始碼到編輯緩衝區 | `LOAD test_a.sc` |
| **`SAVE <file>`** | 將當前緩衝區的原始碼儲存到指定檔案 | `SAVE my_code.sc` |
| **`LIST`** | 列出目前緩衝區的所有程式碼，前方標註行號 | `LIST` |
| **`LIST <n>`** | 顯示緩衝區第 `n` 行程式碼 | `LIST 12` |
| **`LIST <n1>-<n2>`**| 顯示緩衝區第 `n1` 行至第 `n2` 行程式碼 | `LIST 5-15` |
| **`EDIT <n>`** | 編輯第 `n` 行程式碼。若不修改，直接按 Enter 鍵 | `EDIT 25` |
| **`DELETE <n>`** | 刪除第 `n` 行程式碼，之後行號會自動遞減遞補 | `DELETE 10` |
| **`DELETE <n1>-<n2>`**| 刪除第 `n1` 行至第 `n2` 行程式碼 | `DELETE 10-15` |
| **`INSERT <n>`** | 在第 `n` 行前進入插入模式，逐行輸入，輸入單獨 `.` 結束 | `INSERT 3` |
| **`APPEND`** | 在程式末端進入追加模式，逐行輸入，輸入單獨 `.` 結束 | `APPEND` |
| **`NEW`** | 清空緩衝區，並重置解譯器變數與狀態 | `NEW` |
| **`RUN`** | 編譯緩衝區程式碼並從 `main()` 執行 | `RUN` |
| **`CHECK`** | 僅進行編譯與語法/語意錯誤檢查，不執行程式 | `CHECK` |
| **`TRACE ON/OFF`**| 開啟或關閉執行追蹤（RUN 時會顯示當前執行的行號與程式）| `TRACE ON` |
| **`VARS`** | 列出當前環境中所有已宣告的全域/區域變數及其記憶體值 | `VARS` |
| **`FUNCS`** | 列出所有使用者自定義的函式與內建函式簽名 | `FUNCS` |
| **`CLEAR`** | 清除終端機畫面 | `CLEAR` |
| **`HELP [cmd]`** | 顯示指令的詳細說明 | `HELP LOAD` |
| **`QUIT / EXIT`** | 結束 Small-C 解譯器 | `QUIT` |

---

## 執行與使用教學

### 1. 啟動互動式解譯器 (REPL)
請確保本機已安裝 **Python 3.10** 以上版本。在專案目錄下開啟終端機（PowerShell 或 Command Prompt），執行：
```bash
python main.py
```
啟動後會顯示歡迎畫面並進入 `sc>` 提示字元。

### 2. 即時互動執行測試 (Direct Mode)
在 `sc>` 提示符下直接輸入變數宣告、指定與表達式，會立即被解析並印出結果。如果輸入左大括號 `{` 進入多行區塊，提示符會自動轉換為 `  > `，直到括號閉合：
```c
sc> int a = 25;
sc> int b = -18;
sc> printf("a + b = %d\n", a + b);
a + b = 7
sc> if (a > b) {
  >     printf("a is larger\n");
  > }
a is larger
sc> VARS
global int a = 25
global int b = -18
```

### 3. 編寫與執行緩衝區程式碼
可使用 `APPEND` 手動編寫程式，或直接 `LOAD` 檔案：
```c
sc> APPEND
   1> int main() {
   2>     int i;
   3>     for (i = 1; i <= 5; i = i + 1) {
   4>         printf("%d ", i);
   5>     }
   6>     printf("\n");
   7>     return 0;
   8> }
   9> .
sc> LIST
   1> int main() {
   2>     int i;
   3>     for (i = 1; i <= 5; i = i + 1) {
   4>         printf("%d ", i);
   5>     }
   6>     printf("\n");
   7>     return 0;
   8> }
sc> RUN
1 2 3 4 5 
Program exited with return value 0.
```

### 4. 單步追蹤執行
```c
sc> TRACE ON
Trace mode enabled.
sc> RUN
[line 1] int main() {
[line 3] for (i = 1; i <= 5; i = i + 1) {
[line 4] printf("%d ", i);
1 [line 3] for (i = 1; i <= 5; i = i + 1) {
[line 4] printf("%d ", i);
2 [line 3] for (i = 1; i <= 5; i = i + 1) {
...
[line 6] printf("\n");

[line 7] return 0;
Program exited with return value 0.
```

### 5. 直接執行 Small-C 原始碼檔案
如果不希望進入 REPL 互動介面，可以直接在作業系統終端機執行檔案並在執行完後直接退出：
```bash
python main.py test_a.sc
```
這會載入 `test_a.sc`，自動編譯、執行 `main()`，並在終端印出輸出後退出。
