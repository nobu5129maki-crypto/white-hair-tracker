    const input = document.getElementById('camera-input');
    const loading = document.getElementById('loading');
    const resultDisplay = document.getElementById('result-display');
    let myChart;

    function rgbToHsv(r, g, b) {
        r /= 255; g /= 255; b /= 255;
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        const d = max - min;
        let h = 0;
        const s = max === 0 ? 0 : (d / max) * 100;
        const v = max * 100;
        if (d > 0) {
            if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
            else if (max === g) h = ((b - r) / d + 2) / 6;
            else h = ((r - g) / d + 4) / 6;
        }
        return { h: h * 360, s, v };
    }

    function isSkin(h, s, v) {
        return h <= 50 && s >= 10 && s <= 65 && v >= 30 && v <= 90;
    }

    // 白髪判定の明度しきい値（0〜255）。Otsu が使えない（髪色が一様な）場合に使う絶対基準
    const WHITE_V_MIN = 150;
    // Otsu で2クラスに分けたとき、クラス平均の差がこれ未満なら「一様な髪色」とみなす
    const MIN_CLASS_SEPARATION = 60;
    // Otsu のしきい値として妥当な範囲（暗い髪 / 白髪の境目として現実的な明度）
    const OTSU_MIN = 120, OTSU_MAX = 180;
    // 髪として検出できた画素がこれ未満なら判定不能
    const MIN_HAIR_SAMPLES = 100;
    // これ未満なら結果は出すが「髪の領域が小さい」と注意を出す
    const LOW_HAIR_SAMPLES = 3000;
    // 近傍の明度のばらつきがこれ未満なら、毛筋のない平坦な背景とみなす（0〜255）
    const TEXTURE_RADIUS = 3;
    const TEXTURE_STD_MIN = 4;
    // 平坦な画素が候補のこの割合以上なら、背景を除外したことを知らせる
    const FLAT_WARN_RATIO = 0.35;
    const MAX_IMAGE_BYTES = 25 * 1024 * 1024;

    function otsuThreshold(hist, total) {
        let sum = 0;
        for (let i = 0; i < 256; i++) sum += i * hist[i];
        let sumB = 0, wB = 0, maxVar = 0, threshold = 128, bestMB = 0, bestMF = 0;
        for (let t = 0; t < 256; t++) {
            wB += hist[t];
            if (wB === 0) continue;
            const wF = total - wB;
            if (wF === 0) break;
            sumB += t * hist[t];
            const mB = sumB / wB;
            const mF = (sum - sumB) / wF;
            const varBetween = wB * wF * (mB - mF) ** 2;
            if (varBetween > maxVar) { maxVar = varBetween; threshold = t; bestMB = mB; bestMF = mF; }
        }
        return { threshold, meanDark: bestMB, meanLight: bestMF };
    }

    /**
     * 白髪/黒髪を分ける明度しきい値を決める。
     * Otsu 法は必ず2クラスに分けてしまうため、真っ黒な髪でも半分近くが「白髪」と判定されていた。
     * クラス間の差が小さい（髪色が一様）ときは絶対基準 WHITE_V_MIN を使い、
     * 差が大きいときだけ Otsu の値を妥当な範囲に丸めて使う。
     */
    function decideThreshold(hist, total) {
        const { threshold, meanDark, meanLight } = otsuThreshold(hist, total);
        if (meanLight - meanDark < MIN_CLASS_SEPARATION) return WHITE_V_MIN;
        return Math.min(OTSU_MAX, Math.max(OTSU_MIN, threshold));
    }

    function isHairCandidate(h, s, v) {
        if (isSkin(h, s, v)) return false;
        return s <= 40;
    }

    function analyzeImage(file) {
        return new Promise((resolve, reject) => {
            if (file.size > MAX_IMAGE_BYTES) {
                reject(new Error('画像が大きすぎます。25MB以下の写真を選んでください'));
                return;
            }
            const img = new Image();
            const url = URL.createObjectURL(file);
            img.onload = () => {
                URL.revokeObjectURL(url);
                try {
                    resolve(measureWhiteHair(img));
                } catch (err) {
                    reject(err instanceof Error ? err : new Error('解析に失敗しました'));
                }
            };
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('画像を読み込めません。JPEGまたはPNG形式で撮影してください'));
            };
            img.src = url;
        });
    }

    /**
     * 画面中央の髪候補から白髪率を出す。
     * 白い壁のように平坦な領域は白髪と区別できないため、毛筋（明度のばらつき）がある画素だけを使う。
     * 毛筋がほぼ無い写真は、以前は白い壁を白髪100%と保存していたので、結果を出さずエラーにする。
     */
    function measureWhiteHair(img) {
        if (!img.width || !img.height) {
            throw new Error('画像を読み込めません。JPEGまたはPNG形式で撮影してください');
        }
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        // 小さい写真を引き伸ばすと、わずかしか写っていない髪を十分な量と誤認する
        const scale = Math.min(1, 640 / img.width, 640 / img.height);
        const w = Math.max(1, Math.floor(img.width * scale));
        const h = Math.max(1, Math.floor(img.height * scale));
        canvas.width = w;
        canvas.height = h;
        ctx.drawImage(img, 0, 0, w, h);
        const pixels = ctx.getImageData(0, 0, w, h).data;

        const luma = new Float32Array(w * h);
        const cand = new Uint8Array(w * h);
        for (let p = 0, i = 0; p < w * h; p++, i += 4) {
            const hsv = rgbToHsv(pixels[i], pixels[i + 1], pixels[i + 2]);
            luma[p] = Math.min(255, Math.round(hsv.v * 2.55));
            cand[p] = isHairCandidate(hsv.h, hsv.s, hsv.v) ? 1 : 0;
        }

        const rad = TEXTURE_RADIUS;
        const iw = w + 1;
        const integral = new Float64Array((w + 1) * (h + 1));
        const integralSq = new Float64Array((w + 1) * (h + 1));
        for (let y = 1; y <= h; y++) {
            for (let x = 1; x <= w; x++) {
                const v = luma[(y - 1) * w + (x - 1)];
                const idx = y * iw + x;
                const up = (y - 1) * iw + x;
                const left = y * iw + (x - 1);
                const diag = (y - 1) * iw + (x - 1);
                integral[idx] = v + integral[up] + integral[left] - integral[diag];
                integralSq[idx] = v * v + integralSq[up] + integralSq[left] - integralSq[diag];
            }
        }

        function stdAt(x, y) {
            const x1 = Math.max(0, x - rad);
            const y1 = Math.max(0, y - rad);
            const x2 = Math.min(w - 1, x + rad);
            const y2 = Math.min(h - 1, y + rad);
            const a = y1 * iw + x1;
            const b = y1 * iw + (x2 + 1);
            const c = (y2 + 1) * iw + x1;
            const e = (y2 + 1) * iw + (x2 + 1);
            const n = (x2 - x1 + 1) * (y2 - y1 + 1);
            const sum = integral[e] - integral[b] - integral[c] + integral[a];
            const sumSq = integralSq[e] - integralSq[b] - integralSq[c] + integralSq[a];
            const mean = sum / n;
            return Math.sqrt(Math.max(0, sumSq / n - mean * mean));
        }

        const roiX = Math.floor(w * 0.125);
        const roiY = Math.floor(h * 0.15);
        const roiW = Math.floor(w * 0.75);
        const roiH = Math.floor(h * 0.55);
        const histAll = new Array(256).fill(0);
        const histTex = new Array(256).fill(0);
        let allCount = 0;
        let texCount = 0;

        for (let y = roiY; y < roiY + roiH; y++) {
            for (let x = roiX; x < roiX + roiW; x++) {
                const p = y * w + x;
                if (!cand[p]) continue;
                const v = luma[p];
                histAll[v]++;
                allCount++;
                if (stdAt(x, y) >= TEXTURE_STD_MIN) {
                    histTex[v]++;
                    texCount++;
                }
            }
        }

        if (allCount < MIN_HAIR_SAMPLES) {
            throw new Error('髪を検出できませんでした。髪が画面中央に大きく写るように撮り直してください');
        }
        if (texCount < MIN_HAIR_SAMPLES && texCount * 20 < allCount) {
            throw new Error('髪の質感を検出できませんでした。毛筋が分かる明るさで、画面中央に髪を大きく撮ってください');
        }

        const useTexture = texCount >= MIN_HAIR_SAMPLES;
        const hist = useTexture ? histTex : histAll;
        const hairSamples = useTexture ? texCount : allCount;
        const threshold = decideThreshold(hist, hairSamples);
        let whiteCount = 0;
        for (let i = threshold; i < 256; i++) whiteCount += hist[i];
        const flatCount = allCount - texCount;
        return {
            ratio: Math.round((whiteCount / hairSamples) * 1000) / 10,
            hairSamples,
            flatExcluded: useTexture && flatCount / allCount >= FLAT_WARN_RATIO
        };
    }

    function init(attempt) {
        if (typeof Chart !== 'undefined') {
            updateChart();
            return;
        }
        if ((attempt || 0) > 40) return;
        setTimeout(() => init((attempt || 0) + 1), 50);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => init(0));
    else init(0);

    function toggleTips() {
        const toggle = document.getElementById('tips-toggle');
        const content = document.getElementById('tips-content');
        const open = toggle.classList.toggle('open');
        content.classList.toggle('open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        content.setAttribute('aria-hidden', open ? 'false' : 'true');
    }
    document.getElementById('tips-toggle').addEventListener('click', toggleTips);
    document.getElementById('tips-toggle').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleTips(); }
    });

    input.onchange = async (e) => {
        const file = e.target.files[0];
        // 同じ写真を続けて選んでも onchange が発火するようにリセット
        e.target.value = '';
        if (!file) return;
        loading.style.display = 'block';
        resultDisplay.style.display = 'none';
        try {
            const { ratio, hairSamples, flatExcluded } = await analyzeImage(file);
            document.getElementById('ratio').innerText = ratio;
            document.getElementById('advice').innerText = hairSamples < LOW_HAIR_SAMPLES
                ? '髪の領域が小さめです。もう少し近づいて撮ると精度が上がります'
                : (flatExcluded ? '平坦な背景は除外して計算しました。髪を画面いっぱいに撮ると、より安定します' : '');
            resultDisplay.style.display = 'block';
            saveData(ratio);
        } catch (err) {
            alert(err.message || 'エラーが発生しました');
        } finally {
            loading.style.display = 'none';
        }
    };

    function loadHistory() {
        try {
            const parsed = JSON.parse(localStorage.getItem('hairHistory') || '[]');
            if (!Array.isArray(parsed)) throw new Error('invalid');
            return parsed
                .filter((item) => item && Number.isFinite(Number(item.ratio)) && typeof item.date === 'string')
                .map((item) => ({ date: item.date, ratio: Number(item.ratio) }));
        } catch (err) {
            localStorage.removeItem('hairHistory');
            return [];
        }
    }

    function saveData(ratio) {
        const history = loadHistory();
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        const ss = String(now.getSeconds()).padStart(2, '0');
        history.push({ date: (now.getMonth() + 1) + '/' + now.getDate() + ' ' + hh + ':' + mm + ':' + ss, ratio: ratio });
        if (history.length > 10) history.shift();
        localStorage.setItem('hairHistory', JSON.stringify(history));
        updateChart();
    }

    function updateChart() {
        const history = loadHistory();
        const canvas = document.getElementById('historyChart');
        if (!canvas || typeof Chart === 'undefined') return;
        const ctx = canvas.getContext('2d');
        if (myChart) myChart.destroy();
        myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.map(h => h.date),
                datasets: [{
                    label: '白髪率 (%)',
                    data: history.map(h => h.ratio),
                    borderColor: '#4fd1c5',
                    backgroundColor: 'rgba(79, 209, 197, 0.2)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: '#333' },
                        ticks: { color: '#aaa', stepSize: 20, callback: (value) => value + '%' }
                    },
                    x: { grid: { display: false }, ticks: { color: '#aaa', maxRotation: 0, autoSkip: true, maxTicksLimit: 5 } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    function clearData() {
        if (confirm("全ての履歴を消去しますか？")) {
            localStorage.removeItem('hairHistory');
            updateChart();
            resultDisplay.style.display = 'none';
        }
    }
