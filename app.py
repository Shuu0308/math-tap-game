from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>数式タッチゲーム</title>
<style>
body {
    font-family: sans-serif;
    background: #f0f4ff;
    color: #24304a;
    text-align: center;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 600px;
    margin: auto;
}
h1 { color: #5146d8; }
.info {
    display: flex;
    justify-content: space-around;
    margin: 20px 0;
    gap: 10px;
}
.info div {
    background: white;
    padding: 12px;
    border-radius: 12px;
    flex: 1;
}
.value {
    font-size: 24px;
    font-weight: bold;
}
#board {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 7px;
}
.cell {
    min-width: 0;
    min-height: 65px;
    border: none;
    border-radius: 12px;
    background: white;
    box-shadow: 0 3px 0 #d4daf0;
    font-size: clamp(13px, 3.5vw, 20px);
    font-weight: bold;
    overflow-wrap: anywhere;
    cursor: pointer;
    color: #29365a;
}
.cell:disabled { cursor: default; }
.cell.done {
    background: #c8f7d5;
    color: #237a43;
    box-shadow: none;
}
.cell.wrong { background: #ffd5d5; }
button.action {
    border: none;
    border-radius: 12px;
    padding: 13px 24px;
    margin: 10px 5px;
    background: #5146d8;
    color: white;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}
#message {
    min-height: 28px;
    font-weight: bold;
}
@media (max-width: 420px) {
    body { padding: 10px; }
    #board { gap: 5px; }
    .cell { min-height: 58px; }
}
</style>
</head>
<body>
<div class="container">
    <h1>🧮 数式タッチ</h1>
    <p>答えが小さい数式から順番にタッチしよう！</p>

    <div class="info">
        <div>
            <div>次の答え</div>
            <div class="value" id="next">1/4</div>
        </div>
        <div>
            <div>タイム</div>
            <div class="value" id="time">0.00</div>
        </div>
        <div>
            <div>ペナルティ</div>
            <div class="value" id="penalty">+2秒</div>
        </div>
    </div>

    <div id="board"></div>
    <p id="message">スタートを押して挑戦しよう！</p>
    <button class="action" id="start">▶ スタート</button>
    <button class="action" id="reset">↻ リセット</button>
</div>

<script>
const board = document.getElementById("board");
const nextDisplay = document.getElementById("next");
const timeDisplay = document.getElementById("time");
const message = document.getElementById("message");
const startButton = document.getElementById("start");
const resetButton = document.getElementById("reset");
const penaltyDisplay = document.getElementById("penalty");

const penaltySeconds = 2;
penaltyDisplay.textContent = "+" + penaltySeconds + "秒";

let questions = [];
let buttons = [];
let nextIndex = 0;
let startTime = 0;
let elapsedPenalty = 0;
let timer = null;
let playing = false;

function gcd(a, b) {
    a = Math.abs(a);
    b = Math.abs(b);
    while (b !== 0) {
        const r = a % b;
        a = b;
        b = r;
    }
    return a || 1;
}

function makeQuestion(n) {
    const type = Math.floor(Math.random() * 4);
    let a, b, numerator, denominator, text;

    if (n === 0) {
        return { value: 0.25, label: "1÷4" };
    }
    if (n === 1) {
        return { value: 0.5, label: "1÷2" };
    }

    if (type === 0) {
        a = Math.floor(Math.random() * 20) + 1;
        b = Math.floor(Math.random() * 20) + 1;
        return { value: a + b, label: `${a}+${b}` };
    }

    if (type === 1) {
        a = Math.floor(Math.random() * 25) + 1;
        b = Math.floor(Math.random() * a) + 1;
        return { value: a - b, label: `${a}−${b}` };
    }

    if (type === 2) {
        a = Math.floor(Math.random() * 9) + 1;
        b = Math.floor(Math.random() * 9) + 1;
        return { value: a * b, label: `${a}×${b}` };
    }

    a = Math.floor(Math.random() * 24) + 1;
    b = Math.floor(Math.random() * 12) + 1;
    numerator = a;
    denominator = b;
    const d = gcd(numerator, denominator);
    numerator /= d;
    denominator /= d;

    text = denominator === 1
        ? `${numerator}`
        : `${a}÷${b}`;

    return {
        value: a / b,
        label: text
    };
}

function createQuestions() {
    const values = new Set();
    questions = [];

    // 0.25、0.5を含め、答えが重ならない問題を作る
    questions.push(makeQuestion(0));
    questions.push(makeQuestion(1));
    values.add("0.25");
    values.add("0.5");

    let attempts = 0;
    while (questions.length < 25 && attempts < 10000) {
        attempts++;
        const q = makeQuestion(2);
        const key = String(Math.round(q.value * 1000000) / 1000000);

        if (values.has(key)) continue;
        values.add(key);
        questions.push(q);
    }

    questions.sort((a, b) => a.value - b.value);

    // 答えの順番は保持して、盤面の配置だけシャッフル
    const displayQuestions = [...questions];
    for (let i = displayQuestions.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [displayQuestions[i], displayQuestions[j]] =
            [displayQuestions[j], displayQuestions[i]];
    }

    board.innerHTML = "";
    buttons = [];

    displayQuestions.forEach(q => {
        const button = document.createElement("button");
        button.className = "cell";
        button.textContent = q.label;
        button.disabled = true;
        button.addEventListener("click", () => handleClick(q, button));
        board.appendChild(button);
        buttons.push(button);
    });
}

function formatAnswer(value) {
    if (Math.abs(value - 0.25) < 0.000001) return "1/4";
    if (Math.abs(value - 0.5) < 0.000001) return "1/2";
    if (Number.isInteger(value)) return String(value);
    return String(Number(value.toFixed(3)));
}

function handleClick(q, button) {
    if (!playing) return;

    const expected = questions[nextIndex];

    if (q === expected) {
        button.classList.add("done");
        button.disabled = true;
        nextIndex++;

        if (nextIndex >= questions.length) {
            finishGame();
        } else {
            nextDisplay.textContent = formatAnswer(questions[nextIndex].value);
            message.textContent = "正解！その調子！";
        }
    } else {
        elapsedPenalty += penaltySeconds;
        button.classList.add("wrong");
        message.textContent = `順番が違うよ！ +${penaltySeconds}秒`;
        setTimeout(() => button.classList.remove("wrong"), 250);
    }
}

function updateTime() {
    if (!playing) return;
    const elapsed = (Date.now() - startTime) / 1000 + elapsedPenalty;
    timeDisplay.textContent = elapsed.toFixed(2);
}

function finishGame() {
    playing = false;
    clearInterval(timer);
    timer = null;
    updateFinalTime();
    buttons.forEach(button => button.disabled = true);
    startButton.textContent = "▶ もう一度遊ぶ";
    message.textContent = "🎉 クリア！おめでとう！";
}

function updateFinalTime() {
    const elapsed = (Date.now() - startTime) / 1000 + elapsedPenalty;
    timeDisplay.textContent = elapsed.toFixed(2);
}

function startGame() {
    clearInterval(timer);
    createQuestions();
    nextIndex = 0;
    elapsedPenalty = 0;
    startTime = Date.now();
    playing = true;

    nextDisplay.textContent = formatAnswer(questions[0].value);
    timeDisplay.textContent = "0.00";
    message.textContent = "小さい答えからタッチ！";
    startButton.textContent = "▶ プレイ中";
    buttons.forEach(button => button.disabled = false);

    timer = setInterval(updateTime, 50);
}

function resetGame() {
    clearInterval(timer);
    timer = null;
    playing = false;
    nextIndex = 0;
    elapsedPenalty = 0;
    createQuestions();
    nextDisplay.textContent = formatAnswer(questions[0].value);
    timeDisplay.textContent = "0.00";
    message.textContent = "スタートを押して挑戦しよう！";
    startButton.textContent = "▶ スタート";
    buttons.forEach(button => button.disabled = true);
}

startButton.addEventListener("click", startGame);
resetButton.addEventListener("click", resetGame);

createQuestions();
nextDisplay.textContent = formatAnswer(questions[0].value);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True)
