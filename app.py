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
#difficulty {
    padding: 8px;
    margin: 8px;
    border: 2px solid #d4daf0;
    border-radius: 8px;
    font-size: 16px;
}
.info {
    display: flex;
    justify-content: space-around;
    margin: 20px 0;
    gap: 10px;
}
.info div {
    background: white;
    padding: 12px 5px;
    border-radius: 12px;
    flex: 1;
    min-width: 0;
}
.value {
    font-size: clamp(17px, 4vw, 24px);
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
    font-size: clamp(12px, 3.5vw, 20px);
    font-weight: bold;
    overflow-wrap: anywhere;
    cursor: pointer;
    color: #29365a;
    padding: 3px;
}
.cell:disabled { cursor: default; }
.cell.correct-pop {
    animation: correctPop 0.32s ease;
}
.cell.wrong {
    animation: wrongShake 0.28s ease;
}
@keyframes correctPop {
    0% { transform: scale(1); }
    45% { transform: scale(1.12); box-shadow: 0 0 0 5px #b8f4c8; }
    100% { transform: scale(1); }
}
@keyframes wrongShake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    50% { transform: translateX(5px); }
    75% { transform: translateX(-3px); }
}
body.clear-flash {
    animation: clearFlash 0.65s ease;
}
@keyframes clearFlash {
    0%, 100% { background: #f0f4ff; }
    35% { background: #fff1a8; }
    70% { background: #d5ffe2; }
}
#celebration {
    position: fixed;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: 10;
}
.confetti {
    position: absolute;
    top: -20px;
    width: 10px;
    height: 16px;
    border-radius: 2px;
    animation: confettiFall 1.8s linear forwards;
}
@keyframes confettiFall {
    to { transform: translateY(110vh) rotate(720deg); opacity: 0; }
}
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
button.action:disabled {
    opacity: 0.6;
    cursor: default;
}
#message {
    min-height: 28px;
    font-weight: bold;
}
@media (max-width: 420px) {
    body { padding: 10px; }
    #board { gap: 5px; }
    .cell { min-height: 58px; }
    .info div { padding: 10px 3px; }
}
</style>
</head>
<body>
<div class="container">
    <h1>🧮 数式タッチ</h1>
    <p>答えが小さい数式から順番にタッチしよう！</p>

    <label for="difficulty">難易度：</label>
    <select id="difficulty">
        <option value="easy">初級</option>
        <option value="normal" selected>中級</option>
        <option value="hard">上級</option>
        <option value="expert">最上級</option>
    </select>

    <div class="info">
        <div>
            <div>次の答え</div>
            <div class="value" id="next">-</div>
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
    <div id="celebration" aria-hidden="true"></div>
    <button class="action" id="start">▶ スタート</button>
    <button class="action" id="reset">↻ リセット</button>
    <button class="action" id="soundToggle" type="button">🔊 効果音 ON</button>
</div>

<script>
const board = document.getElementById("board");
const nextDisplay = document.getElementById("next");
const timeDisplay = document.getElementById("time");
const message = document.getElementById("message");
const startButton = document.getElementById("start");
const resetButton = document.getElementById("reset");
const penaltyDisplay = document.getElementById("penalty");
const difficultySelect = document.getElementById("difficulty");
const soundToggle = document.getElementById("soundToggle");
const celebration = document.getElementById("celebration");

const penaltySeconds = 2;
penaltyDisplay.textContent = "+" + penaltySeconds + "秒";

let questions = [];
let buttons = [];
let nextIndex = 0;
let startTime = 0;
let elapsedPenalty = 0;
let timer = null;
let playing = false;
let soundEnabled = true;
let audioContext = null;

function playTone(frequency, duration = 0.12, type = "sine", volume = 0.06, delay = 0) {
    if (!soundEnabled) return;

    try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;

        if (!audioContext) audioContext = new AudioContextClass();
        if (audioContext.state === "suspended") audioContext.resume();

        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        const startAt = audioContext.currentTime + delay;

        oscillator.type = type;
        oscillator.frequency.setValueAtTime(frequency, startAt);
        gain.gain.setValueAtTime(0.0001, startAt);
        gain.gain.exponentialRampToValueAtTime(volume, startAt + 0.015);
        gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

        oscillator.connect(gain);
        gain.connect(audioContext.destination);
        oscillator.start(startAt);
        oscillator.stop(startAt + duration + 0.02);
    } catch (error) {
        // 効果音が使えない環境でもゲームは続けられる
    }
}

function playCorrectSound() {
    playTone(660, 0.09, "sine", 0.055);
    playTone(880, 0.12, "sine", 0.05, 0.08);
}

function playWrongSound() {
    playTone(180, 0.18, "square", 0.035);
}

function playClearSound() {
    playTone(523, 0.16, "sine", 0.06, 0);
    playTone(659, 0.16, "sine", 0.06, 0.14);
    playTone(784, 0.16, "sine", 0.06, 0.28);
    playTone(1047, 0.32, "sine", 0.07, 0.42);
}

function showConfetti() {
    celebration.innerHTML = "";
    const colors = ["#ff5d8f", "#ffc857", "#55d6be", "#7b61ff", "#4da3ff"];
    for (let i = 0; i < 90; i++) {
        const piece = document.createElement("span");
        piece.className = "confetti";
        piece.style.left = Math.random() * 100 + "%";
        piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = (Math.random() * 0.7) + "s";
        piece.style.transform = "rotate(" + Math.floor(Math.random() * 360) + "deg)";
        celebration.appendChild(piece);
    }
    window.setTimeout(() => {
        celebration.innerHTML = "";
    }, 2800);
}

function makeQuestion() {
    const difficulty = difficultySelect.value;
    let a, b, c, type;

    // 初級：足し算・引き算
    if (difficulty === "easy") {
        type = Math.floor(Math.random() * 2);

        if (type === 0) {
            a = Math.floor(Math.random() * 20) + 1;
            b = Math.floor(Math.random() * 20) + 1;
            return {
                value: a + b,
                label: `${a}+${b}`
            };
        }

        a = Math.floor(Math.random() * 25) + 1;
        b = Math.floor(Math.random() * a) + 1;
        return {
            value: a - b,
            label: `${a}−${b}`
        };
    }

    // 中級：四則演算
    if (difficulty === "normal") {
        type = Math.floor(Math.random() * 4);

        if (type === 0) {
            a = Math.floor(Math.random() * 20) + 1;
            b = Math.floor(Math.random() * 20) + 1;
            return {
                value: a + b,
                label: `${a}+${b}`
            };
        }

        if (type === 1) {
            a = Math.floor(Math.random() * 25) + 1;
            b = Math.floor(Math.random() * a) + 1;
            return {
                value: a - b,
                label: `${a}−${b}`
            };
        }

        if (type === 2) {
            a = Math.floor(Math.random() * 9) + 1;
            b = Math.floor(Math.random() * 9) + 1;
            return {
                value: a * b,
                label: `${a}×${b}`
            };
        }

        a = Math.floor(Math.random() * 24) + 1;
        b = Math.floor(Math.random() * 12) + 1;
        return {
            value: a / b,
            label: `${a}÷${b}`
        };
    }

    // 上級：複数の演算を組み合わせる
    if (difficulty === "hard") {
        a = Math.floor(Math.random() * 9) + 1;
        b = Math.floor(Math.random() * 9) + 1;
        c = Math.floor(Math.random() * 9) + 1;

        type = Math.floor(Math.random() * 3);

        if (type === 0) {
            return {
                value: a + b * c,
                label: `${a}+${b}×${c}`
            };
        }

        if (type === 1) {
            return {
                value: (a + b) * c,
                label: `(${a}+${b})×${c}`
            };
        }

        return {
            value: a * (b + c),
            label: `${a}×(${b}+${c})`
        };
    }

    // 最上級：括弧を使った計算
    a = Math.floor(Math.random() * 9) + 1;
    b = Math.floor(Math.random() * 9) + 1;
    c = Math.floor(Math.random() * 9) + 1;

    type = Math.floor(Math.random() * 4);

    if (type === 0) {
        return {
            value: (a + b) * c,
            label: `(${a}+${b})×${c}`
        };
    }

    if (type === 1) {
        return {
            value: (a + b) / c,
            label: `(${a}+${b})÷${c}`
        };
    }

    if (type === 2) {
        return {
            value: a * (b + c),
            label: `${a}×(${b}+${c})`
        };
    }

    return {
        value: (a + b) * (c + 1),
        label: `(${a}+${b})×(${c}+1)`
    };
}

function createQuestions() {
    const values = new Set();
    questions = [];

    // 答えが重ならないように25問作る
    let attempts = 0;

    while (questions.length < 25 && attempts < 50000) {
        attempts++;

        const q = makeQuestion();
        const key = String(Math.round(q.value * 1000000) / 1000000);

        if (!Number.isFinite(q.value) || values.has(key)) {
            continue;
        }

        values.add(key);
        questions.push(q);
    }

    if (questions.length < 25) {
        message.textContent =
            "問題を十分に作れませんでした。もう一度お試しください。";
        return false;
    }

    // 答えの小さい順に並べる
    questions.sort((a, b) => a.value - b.value);

    // 盤面に表示する順番だけシャッフルする
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

        button.addEventListener("click", () => {
            handleClick(q, button);
        });

        board.appendChild(button);
        buttons.push(button);
    });

    return true;
}

function formatAnswer(value) {
    if (Number.isInteger(value)) {
        return String(value);
    }

    return String(Number(value.toFixed(3)));
}

function handleClick(q, button) {
    if (!playing) return;

    const expected = questions[nextIndex];

    if (q === expected) {
        playCorrectSound();
        button.classList.add("done", "correct-pop");
        button.disabled = true;
        window.setTimeout(() => button.classList.remove("correct-pop"), 350);
        nextIndex++;

        if (nextIndex >= questions.length) {
            finishGame();
        } else {
            nextDisplay.textContent =
                formatAnswer(questions[nextIndex].value);
            message.textContent = "正解！その調子！";
        }
    } else {
        playWrongSound();
        elapsedPenalty += penaltySeconds;
        button.classList.add("wrong");
        message.textContent =
            `順番が違うよ！ +${penaltySeconds}秒`;

        setTimeout(() => {
            button.classList.remove("wrong");
        }, 300);

        updateTime();
    }
}

function updateTime() {
    if (!playing) return;

    const elapsed =
        (Date.now() - startTime) / 1000 + elapsedPenalty;

    timeDisplay.textContent = elapsed.toFixed(2);
}

function finishGame() {
    playing = false;
    clearInterval(timer);
    timer = null;

    updateFinalTime();

    buttons.forEach(button => {
        button.disabled = true;
    });

    startButton.textContent = "▶ もう一度遊ぶ";
    message.textContent = "🎉 クリア！おめでとう！";
    document.body.classList.remove("clear-flash");
    void document.body.offsetWidth;
    document.body.classList.add("clear-flash");
    playClearSound();
    showConfetti();
}

function updateFinalTime() {
    const elapsed =
        (Date.now() - startTime) / 1000 + elapsedPenalty;

    timeDisplay.textContent = elapsed.toFixed(2);
}

function startGame() {
    clearInterval(timer);
    timer = null;

    if (!createQuestions()) {
        playing = false;
        return;
    }

    nextIndex = 0;
    elapsedPenalty = 0;
    startTime = Date.now();
    playing = true;

    nextDisplay.textContent = formatAnswer(questions[0].value);
    timeDisplay.textContent = "0.00";
    message.textContent = "小さい答えからタッチ！";
    startButton.textContent = "▶ プレイ中";

    buttons.forEach(button => {
        button.disabled = false;
    });

    timer = setInterval(updateTime, 50);
}

function resetGame() {
    clearInterval(timer);
    timer = null;
    playing = false;
    nextIndex = 0;
    elapsedPenalty = 0;

    if (!createQuestions()) {
        nextDisplay.textContent = "-";
        timeDisplay.textContent = "0.00";
        startButton.textContent = "▶ スタート";
        return;
    }

    nextDisplay.textContent = formatAnswer(questions[0].value);
    timeDisplay.textContent = "0.00";
    message.textContent = "スタートを押して挑戦しよう！";
    startButton.textContent = "▶ スタート";

    buttons.forEach(button => {
        button.disabled = true;
    });
}

difficultySelect.addEventListener("change", () => {
    clearInterval(timer);
    timer = null;
    playing = false;
    nextIndex = 0;
    elapsedPenalty = 0;

    resetGame();
    message.textContent = "難易度を選んだよ！スタートしよう！";
});

startButton.addEventListener("click", startGame);
resetButton.addEventListener("click", resetGame);

soundToggle.addEventListener("click", () => {
    soundEnabled = !soundEnabled;
    soundToggle.textContent = soundEnabled ? "🔊 効果音 ON" : "🔇 効果音 OFF";
    if (soundEnabled) playTone(660, 0.1, "sine", 0.05);
});

// 最初の画面を準備する
resetGame();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=False)
