// ============================================================
// app.js - LOGIC DASHBOARD (BAN DOCKER)
// ------------------------------------------------------------
// CHI CHEN THEM (BO SUNG FPS): bien fpsValueEl, cap nhat o FPS
// trong fetchLiveVideoFrame() (da co san, dang polling ~300ms
// trong luc chay) va dat ve "-- FPS" khi Dung/loi/video ket thuc.
// Ngoai ra hien thi them cot FPS trong bang chi tiet cua modal
// "Xuat du lieu chi tiet" (da them san 1 cot <th>FPS</th> trong
// index.html).
//
// CHI CHEN THEM (BO SUNG NGUON YOUTUBE): them 1 lua chon
// "+ Nhap link YouTube" o cuoi dropdown "Nguon ghi hinh". Khi
// chon, hien 1 o nhap link + nut "Xac nhan"; sau khi xac nhan
// thanh cong, hanh vi tiep theo (ve Cross-Line, Bat dau...)
// giong het nhu da chon 1 video local - chi khac o cho video_path
// thuc su la 1 URL stream YouTube (xu ly o app.py + services/
// youtube_service.py). Toan bo phan them moi duoc danh dau ro
// bang comment "CHI CHEN THEM (YOUTUBE)".
// ============================================================
const frameImage = document.getElementById("frameImage");
const overlayCanvas = document.getElementById("overlayCanvas");
const ctx = overlayCanvas.getContext("2d");
const videoPlaceholder = document.getElementById("videoPlaceholder");
const videoStage = document.getElementById("videoStage");

const videoSelect = document.getElementById("videoSelect");
const sourceMsg = document.getElementById("sourceMsg");

// ---- CHI CHEN THEM (YOUTUBE): tham chieu toi o nhap link ----
const youtubeInputGroup = document.getElementById("youtubeInputGroup");
const youtubeUrlInput = document.getElementById("youtubeUrlInput");
const btnConfirmYoutube = document.getElementById("btnConfirmYoutube");
const YOUTUBE_OPTION_VALUE = "__youtube__";

const dbSelect = document.getElementById("dbSelect");
const btnDisconnectDb = document.getElementById("btnDisconnectDb");
const dbMsg = document.getElementById("dbMsg");

const btnPickStart = document.getElementById("btnPickStart");
const btnPickEnd = document.getElementById("btnPickEnd");
const coordStart = document.getElementById("coordStart");
const coordEnd = document.getElementById("coordEnd");
const huong1Input = document.getElementById("huong1Input");
const huong2Input = document.getElementById("huong2Input");

const btnBatDau = document.getElementById("btnBatDau");
const btnTamDung = document.getElementById("btnTamDung");
const btnDung = document.getElementById("btnDung");
const sessionMsg = document.getElementById("sessionMsg");

const thoiGianHienTaiInput = document.getElementById("thoiGianHienTai");
const tuThoiDiemInput = document.getElementById("tuThoiDiem");
const denThoiDiemInput = document.getElementById("denThoiDiem");
const statsHint = document.getElementById("statsHint");
const huong1Header = document.getElementById("huong1Header");
const huong2Header = document.getElementById("huong2Header");

const btnExportDetail = document.getElementById("btnExportDetail");
const detailModal = document.getElementById("detailModal");
const detailRangeInfo = document.getElementById("detailRangeInfo");
const detailSummaryTable = document.getElementById("detailSummaryTable").querySelector("tbody");
const detailListTable = document.getElementById("detailListTable").querySelector("tbody");
const btnDownloadCsv = document.getElementById("btnDownloadCsv");
const btnCloseDetailModal = document.getElementById("btnCloseDetailModal");

// ---- CHI CHEN THEM: tham chieu toi o hien thi FPS ----
const fpsValueEl = document.getElementById("fpsValue");

let currentVideoFilename = "";
// ---- CHI CHEN THEM (YOUTUBE): trang thai nguon dang chon ----
let currentSourceType = "local"; // "local" hoac "youtube"
let currentYoutubeUrl = "";

let pickingMode = null;
let point1 = null;
let point2 = null;
let point1Locked = false;
let crosslineLocked = false;
let isPaused = false;
let dbConnectedFlag = false;
let statsPollHandle = null;
let videoFramePollHandle = null;
let naturalWidth = 0, naturalHeight = 0;

const CLASS_KEY_TO_INPUT = {
    bus: { h1: "busH1", h2: "busH2" },
    motorbike: { h1: "motoH1", h2: "motoH2" },
    car: { h1: "carH1", h2: "carH2" },
    truck: { h1: "truckH1", h2: "truckH2" },
};

function setMsg(el, text, cls) {
    el.textContent = text;
    el.className = "msg-line " + (cls || "");
}

function formatDateVN(isoString) {
    if (!isoString) return "";
    const parts = isoString.split(" ");
    if (parts.length !== 2) return isoString;
    const [datePart, timePart] = parts;
    const [yyyy, mm, dd] = datePart.split("-");
    if (!yyyy || !mm || !dd) return isoString;
    return `${dd}-${mm}-${yyyy} ${timePart}`;
}

// ============================================================
// DONG HO "THOI GIAN HIEN TAI" - TICK THEO TUNG GIAY THAT
// ============================================================
let clockBaseDate = null;
let clockBaseFetchedAtMs = 0;

function parseWallClockToUTCDate(isoString) {
    const parts = (isoString || "").split(" ");
    if (parts.length !== 2) return null;
    const [datePart, timePart] = parts;
    const [yyyy, mm, dd] = datePart.split("-").map(Number);
    const [HH, MI, SS] = timePart.split(":").map(Number);
    if ([yyyy, mm, dd, HH, MI, SS].some(n => Number.isNaN(n))) return null;
    return new Date(Date.UTC(yyyy, mm - 1, dd, HH, MI, SS));
}

function formatUTCDateAsVN(dateObj) {
    const dd = String(dateObj.getUTCDate()).padStart(2, "0");
    const mm = String(dateObj.getUTCMonth() + 1).padStart(2, "0");
    const yyyy = dateObj.getUTCFullYear();
    const HH = String(dateObj.getUTCHours()).padStart(2, "0");
    const MI = String(dateObj.getUTCMinutes()).padStart(2, "0");
    const SS = String(dateObj.getUTCSeconds()).padStart(2, "0");
    return `${dd}-${mm}-${yyyy} ${HH}:${MI}:${SS}`;
}

function setServerTimeAnchor(isoString) {
    const parsed = parseWallClockToUTCDate(isoString);
    if (!parsed) return;
    clockBaseDate = parsed;
    clockBaseFetchedAtMs = Date.now();
    tickClock();
}

function tickClock() {
    if (!clockBaseDate) return;
    const elapsedMs = Date.now() - clockBaseFetchedAtMs;
    const displayDate = new Date(clockBaseDate.getTime() + elapsedMs);
    thoiGianHienTaiInput.value = formatUTCDateAsVN(displayDate);
}
setInterval(tickClock, 1000);

// ============================================================
// 1. CHON NGUON VIDEO
// ============================================================
async function loadVideoList() {
    let gia_tri_dang_chon = videoSelect.value;
    try {
        const res = await fetch("/api/video/list");
        const data = await res.json();
        // A user may select a source while the focus-triggered request is in flight.
        gia_tri_dang_chon = videoSelect.value;
        videoSelect.innerHTML = '<option value="">-- Chọn video --</option>';
        if (data.ok) {
            data.files.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f;
                videoSelect.appendChild(opt);
            });
            if (data.files.length === 0) {
                setMsg(sourceMsg, `Thư mục ${data.video_dir} chưa có file video nào.`, "error");
            }
        } else {
            setMsg(sourceMsg, data.message || "Lỗi khi tải danh sách video.", "error");
        }
    } catch (e) {
        setMsg(sourceMsg, "Lỗi kết nối máy chủ khi tải danh sách video.", "error");
    }
    // ============================================================
    // CHI CHEN THEM (YOUTUBE): luon them tuy chon "+ Nhap link
    // YouTube" o cuoi danh sach, moi lan dropdown duoc mo lai (vi
    // innerHTML da bi xoa trang o tren). Khoi phuc lai lua chon
    // dang co truoc do, ke ca khi do chinh la tuy chon nay.
    // ============================================================
    const ytOpt = document.createElement("option");
    ytOpt.value = YOUTUBE_OPTION_VALUE;
    ytOpt.textContent = "+ Nhập link YouTube";
    videoSelect.appendChild(ytOpt);
    if (gia_tri_dang_chon) {
        const matchOpt = Array.from(videoSelect.options).find(o => o.value === gia_tri_dang_chon);
        if (matchOpt) videoSelect.value = gia_tri_dang_chon;
    }
}
videoSelect.addEventListener("mousedown", loadVideoList);
videoSelect.addEventListener("focus", loadVideoList);
videoSelect.addEventListener("change", async () => {
    const filename = videoSelect.value;

    // ---- CHI CHEN THEM (YOUTUBE): hien/an o nhap link tuy chon ----
    if (filename === YOUTUBE_OPTION_VALUE) {
        youtubeInputGroup.classList.add("visible");
        frameImage.style.display = "none";
        overlayCanvas.style.display = "none";
        videoPlaceholder.style.display = "";
        videoPlaceholder.textContent = "Vui lòng dán link YouTube và bấm \"Xác nhận\".";
        setMsg(sourceMsg, "", "");
        return;
    }
    youtubeInputGroup.classList.remove("visible");
    videoPlaceholder.textContent = "";

    if (!filename) return;

    currentSourceType = "local";
    currentYoutubeUrl = "";
    currentVideoFilename = filename;

    setMsg(sourceMsg, "Đang tải khung hình đầu tiên...", "");
    try {
        const frameRes = await fetch("/api/video/first_frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: currentVideoFilename })
        });
        const frameData = await frameRes.json();
        if (!frameData.ok) {
            setMsg(sourceMsg, frameData.message || "Lỗi khi đọc khung hình.", "error");
            return;
        }
        naturalWidth = frameData.width;
        naturalHeight = frameData.height;
        frameImage.src = frameData.image_base64;
        frameImage.onload = () => {
            videoPlaceholder.style.display = "none";
            frameImage.style.display = "block";
            overlayCanvas.style.display = "block";
            resizeCanvasToImage();
        };
        if (!crosslineLocked) {
            resetCrosslineState();
        }
        setMsg(sourceMsg, `Đã tải video: ${currentVideoFilename}`, "success");
    } catch (e) {
        setMsg(sourceMsg, "Lỗi kết nối máy chủ khi tải video.", "error");
    }
});

// ============================================================
// CHI CHEN THEM (YOUTUBE): xu ly khi nguoi dung dan link va bam
// "Xac nhan". Mo phong y het luong xu ly cua videoSelect "change"
// o tren (set naturalWidth/naturalHeight, hien khung hinh, reset
// Cross-Line neu chua khoa), chi khac nguon du lieu la endpoint
// rieng cho YouTube.
// ============================================================
btnConfirmYoutube.addEventListener("click", async () => {
    const url = youtubeUrlInput.value.trim();
    if (!url) {
        setMsg(sourceMsg, "Vui lòng dán link YouTube.", "error");
        return;
    }
    setMsg(sourceMsg, "Đang xử lý link YouTube (có thể mất vài giây)...", "");
    btnConfirmYoutube.disabled = true;
    try {
        const res = await fetch("/api/video/youtube_first_frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ youtube_url: url })
        });
        const data = await res.json();
        if (!data.ok) {
            setMsg(sourceMsg, data.message || "Lỗi khi xử lý link YouTube.", "error");
            return;
        }
        naturalWidth = data.width;
        naturalHeight = data.height;
        currentSourceType = "youtube";
        currentYoutubeUrl = data.youtube_url;
        currentVideoFilename = "";
        frameImage.src = data.image_base64;
        frameImage.onload = () => {
            videoPlaceholder.style.display = "none";
            frameImage.style.display = "block";
            overlayCanvas.style.display = "block";
            resizeCanvasToImage();
        };
        if (!crosslineLocked) {
            resetCrosslineState();
        }
        setMsg(sourceMsg, "Đã tải khung hình đầu tiên từ link YouTube.", "success");
    } catch (e) {
        setMsg(sourceMsg, "Lỗi kết nối máy chủ khi xử lý link YouTube.", "error");
    } finally {
        btnConfirmYoutube.disabled = crosslineLocked;
    }
});

function resizeCanvasToImage() {
    const rect = frameImage.getBoundingClientRect();
    const stageRect = videoStage.getBoundingClientRect();
    overlayCanvas.style.width = rect.width + "px";
    overlayCanvas.style.height = rect.height + "px";
    overlayCanvas.style.left = (rect.left - stageRect.left) + "px";
    overlayCanvas.style.top = (rect.top - stageRect.top) + "px";
    overlayCanvas.width = rect.width;
    overlayCanvas.height = rect.height;
    redrawOverlay();
}
if (window.ResizeObserver) {
    const resizeObserver = new ResizeObserver(() => {
        if (frameImage.style.display === "block") {
            resizeCanvasToImage();
        }
    });
    resizeObserver.observe(videoStage);
}
window.addEventListener("resize", () => {
    if (frameImage.style.display === "block") resizeCanvasToImage();
});

// ============================================================
// 2. CO SO DU LIEU (CSDL) - dropdown inline + Ngat ket noi
// ============================================================
function updateDbDisconnectButtonState() {
    btnDisconnectDb.disabled = crosslineLocked || !dbConnectedFlag;
}
async function loadDbList() {
    try {
        const res = await fetch("/api/db/list");
        const data = await res.json();
        const selectedDatabase = dbSelect.value;
        dbSelect.innerHTML = '<option value="">-- Chọn database --</option>';
        if (data.ok) {
            data.files.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f;
                dbSelect.appendChild(opt);
            });
            if (Array.from(dbSelect.options).some(option => option.value === selectedDatabase)) {
                dbSelect.value = selectedDatabase;
            }
        }
    } catch (e) { /* bo qua */ }
}
async function syncDbSelectorFromStatus() {
    try {
        const res = await fetch("/api/db/status");
        const data = await res.json();
        dbConnectedFlag = !!data.connected;
        if (data.connected && !data.auto_created && data.db_relpath) {
            const matchOpt = Array.from(dbSelect.options).find(o => o.value === data.db_relpath);
            dbSelect.value = matchOpt ? data.db_relpath : "";
        } else {
            dbSelect.value = "";
        }
        if (data.connected) {
            const soBanGhi = data.tong_ban_ghi ?? 0;
            setMsg(
                dbMsg,
                `Đang kết nối (${soBanGhi} bản ghi)` + (data.auto_created ? " - CSDL tự sinh" : ""),
                "success"
            );
        } else {
            setMsg(dbMsg, "Chưa kết nối CSDL nào.", "");
        }
    } catch (e) { /* bo qua */ }
    updateDbDisconnectButtonState();
}
dbSelect.addEventListener("mousedown", loadDbList);
dbSelect.addEventListener("focus", loadDbList);
dbSelect.addEventListener("change", async () => {
    const relPath = dbSelect.value;
    if (!relPath) return;
    setMsg(dbMsg, "Đang kết nối...", "");
    try {
        const res = await fetch("/api/db/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: relPath })
        });
        const data = await res.json();
        if (!data.ok) {
            setMsg(dbMsg, data.message || "Lỗi khi kết nối CSDL.", "error");
            await syncDbSelectorFromStatus();
            return;
        }
        await syncDbSelectorFromStatus();
        fetchLiveStats();
    } catch (e) {
        setMsg(dbMsg, "Lỗi kết nối máy chủ.", "error");
    }
});
btnDisconnectDb.addEventListener("click", async () => {
    try {
        const res = await fetch("/api/db/disconnect", { method: "POST" });
        const data = await res.json();
        if (!data.ok) {
            setMsg(dbMsg, data.message || "Lỗi khi ngắt kết nối.", "error");
            return;
        }
        await syncDbSelectorFromStatus();
        fetchLiveStats();
    } catch (e) {
        setMsg(dbMsg, "Lỗi kết nối máy chủ.", "error");
    }
});

// ============================================================
// 3. CAU HINH CROSS-LINE
// ============================================================
function resetCrosslineState() {
    pickingMode = null;
    point1 = null;
    point2 = null;
    point1Locked = false;
    coordStart.value = "";
    coordEnd.value = "";
    coordStart.readOnly = false;
    huong1Input.value = "";
    huong2Input.value = "";
    btnPickStart.classList.remove("picking");
    btnPickEnd.classList.remove("picking");
    redrawOverlay();
}
btnPickStart.addEventListener("click", () => {
    if (crosslineLocked) return;
    pickingMode = "start";
    point1Locked = false;
    coordStart.readOnly = false;
    btnPickStart.classList.add("picking");
    btnPickEnd.classList.remove("picking");
});
btnPickEnd.addEventListener("click", () => {
    if (crosslineLocked) return;
    pickingMode = "end";
    point1Locked = true;
    coordStart.readOnly = true;
    btnPickEnd.classList.add("picking");
    btnPickStart.classList.remove("picking");
});
function canvasToNaturalCoord(cx, cy) {
    const scaleX = naturalWidth / overlayCanvas.width;
    const scaleY = naturalHeight / overlayCanvas.height;
    return { x: Math.round(cx * scaleX), y: Math.round(cy * scaleY) };
}
function naturalToCanvasCoord(nx, ny) {
    const scaleX = overlayCanvas.width / naturalWidth;
    const scaleY = overlayCanvas.height / naturalHeight;
    return { x: nx * scaleX, y: ny * scaleY };
}
overlayCanvas.addEventListener("click", (e) => {
    if (!pickingMode || crosslineLocked) return;
    const rect = overlayCanvas.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const natural = canvasToNaturalCoord(cx, cy);
    if (pickingMode === "start" && !point1Locked) {
        point1 = natural;
        coordStart.value = `${natural.x}, ${natural.y}`;
    } else if (pickingMode === "end") {
        point2 = natural;
        coordEnd.value = `${natural.x}, ${natural.y}`;
    }
    redrawOverlay();
});
function parseCoordText(text) {
    const parts = text.split(",").map(s => parseFloat(s.trim()));
    if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        return { x: parts[0], y: parts[1] };
    }
    return null;
}
coordStart.addEventListener("change", () => {
    if (point1Locked || crosslineLocked) return;
    const p = parseCoordText(coordStart.value);
    if (p) { point1 = p; redrawOverlay(); }
});
coordEnd.addEventListener("change", () => {
    if (crosslineLocked) return;
    const p = parseCoordText(coordEnd.value);
    if (p) { point2 = p; redrawOverlay(); }
});
function sideValue(p, p1, p2) {
    return (p2.x - p1.x) * (p.y - p1.y) - (p2.y - p1.y) * (p.x - p1.x);
}
function segmentLineIntersection(a, b, p1, p2) {
    const va = sideValue(a, p1, p2);
    const vb = sideValue(b, p1, p2);
    const t = va / (va - vb);
    return { x: a.x + t * (b.x - a.x), y: a.y + t * (b.y - a.y) };
}
function clipPolygonHalfPlane(poly, p1, p2, keepPositive) {
    const output = [];
    const n = poly.length;
    for (let i = 0; i < n; i++) {
        const curr = poly[i];
        const prev = poly[(i - 1 + n) % n];
        const currVal = sideValue(curr, p1, p2);
        const prevVal = sideValue(prev, p1, p2);
        const currInside = keepPositive ? currVal >= 0 : currVal <= 0;
        const prevInside = keepPositive ? prevVal >= 0 : prevVal <= 0;
        if (currInside) {
            if (!prevInside) output.push(segmentLineIntersection(prev, curr, p1, p2));
            output.push(curr);
        } else if (prevInside) {
            output.push(segmentLineIntersection(prev, curr, p1, p2));
        }
    }
    return output;
}
function drawPolygon(poly, fillStyle) {
    if (poly.length < 3) return;
    ctx.beginPath();
    ctx.moveTo(poly[0].x, poly[0].y);
    for (let i = 1; i < poly.length; i++) ctx.lineTo(poly[i].x, poly[i].y);
    ctx.closePath();
    ctx.fillStyle = fillStyle;
    ctx.fill();
}
const CORNER_STYLES = [
    { getPos: (W, H) => ({ x: 10, y: 10 }), align: "left", baseline: "top" },
    { getPos: (W, H) => ({ x: W - 10, y: 10 }), align: "right", baseline: "top" },
    { getPos: (W, H) => ({ x: W - 10, y: H - 10 }), align: "right", baseline: "bottom" },
    { getPos: (W, H) => ({ x: 10, y: H - 10 }), align: "left", baseline: "bottom" },
];
function pickCornerLabelIndexes(W, H, p1, p2) {
    const rawCorners = [
        { x: 0, y: 0 }, { x: W, y: 0 }, { x: W, y: H }, { x: 0, y: H }
    ];
    let bestPosIdx = 0, bestPosVal = -Infinity;
    let bestNegIdx = 0, bestNegVal = Infinity;
    for (let i = 0; i < 4; i++) {
        const val = sideValue(rawCorners[i], p1, p2);
        if (val > bestPosVal) { bestPosVal = val; bestPosIdx = i; }
        if (val < bestNegVal) { bestNegVal = val; bestNegIdx = i; }
    }
    return { huong1Idx: bestPosIdx, huong2Idx: bestNegIdx };
}
function drawCornerLabel(cornerIndex, text, textColor) {
    if (!text) return;
    const style = CORNER_STYLES[cornerIndex];
    const { x, y } = style.getPos(overlayCanvas.width, overlayCanvas.height);
    ctx.font = "bold 13px 'Segoe UI', Arial, sans-serif";
    ctx.textAlign = style.align;
    ctx.textBaseline = style.baseline;
    const metrics = ctx.measureText(text);
    const paddingX = 8, paddingY = 5;
    const textW = metrics.width;
    const textH = 13;
    let boxX = style.align === "left" ? x - paddingX : x - textW - paddingX;
    let boxY = style.baseline === "top" ? y - paddingY : y - textH - paddingY;
    const boxW = textW + paddingX * 2;
    const boxH = textH + paddingY * 2;
    ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(boxX, boxY, boxW, boxH, 4);
        ctx.fill();
    } else {
        ctx.fillRect(boxX, boxY, boxW, boxH);
    }
    ctx.fillStyle = textColor;
    ctx.fillText(text, x, y);
}
function drawPointMarker(p, color, label) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 7, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();
    if (label) {
        ctx.fillStyle = "#fff";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "alphabetic";
        ctx.fillText(label, p.x, p.y + 4);
    }
}
function redrawOverlay() {
    const W = overlayCanvas.width, H = overlayCanvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!W || !H) return;
    if (!point1 || !point2 || !naturalWidth || !naturalHeight) {
        if (point1 && naturalWidth && naturalHeight) {
            const c1 = naturalToCanvasCoord(point1.x, point1.y);
            drawPointMarker(c1, "#2e7d32", "1");
        }
        return;
    }
    const c1 = naturalToCanvasCoord(point1.x, point1.y);
    const c2 = naturalToCanvasCoord(point2.x, point2.y);
    if (crosslineLocked) {
        ctx.beginPath();
        ctx.moveTo(c1.x, c1.y);
        ctx.lineTo(c2.x, c2.y);
        ctx.strokeStyle = "#e53935";
        ctx.lineWidth = 4;
        ctx.stroke();
        drawPointMarker(c1, "#ffc107", null);
        drawPointMarker(c2, "#ffc107", null);
        const { huong1Idx, huong2Idx } = pickCornerLabelIndexes(W, H, c1, c2);
        const huong1Text = huong1Header.textContent || "";
        const huong2Text = huong2Header.textContent || "";
        drawCornerLabel(huong1Idx, huong1Text, "#66ffa6");
        drawCornerLabel(huong2Idx, huong2Text, "#ff8a80");
    } else {
        const rectCorners = [
            { x: 0, y: 0 }, { x: W, y: 0 },
            { x: W, y: H }, { x: 0, y: H }
        ];
        const polyPositive = clipPolygonHalfPlane(rectCorners, c1, c2, true);
        const polyNegative = clipPolygonHalfPlane(rectCorners, c1, c2, false);
        drawPolygon(polyPositive, "rgba(46, 125, 50, 0.30)");
        drawPolygon(polyNegative, "rgba(198, 40, 40, 0.30)");
        ctx.beginPath();
        ctx.moveTo(c1.x, c1.y);
        ctx.lineTo(c2.x, c2.y);
        ctx.strokeStyle = "#212121";
        ctx.lineWidth = 3;
        ctx.stroke();
        drawPointMarker(c1, "#2e7d32", "1");
        drawPointMarker(c2, "#c62828", "2");
    }
}

// ============================================================
// 4. NUT BAT DAU / TAM DUNG / DUNG
// ============================================================
btnBatDau.addEventListener("click", async () => {
    if (!point1 || !point2) {
        setMsg(sessionMsg, "Vui lòng chọn đủ Điểm bắt đầu và Điểm kết thúc.", "error");
        return;
    }
    if (!huong1Input.value.trim() || !huong2Input.value.trim()) {
        setMsg(sessionMsg, "Vui lòng nhập đầy đủ Hướng 1 và Hướng 2.", "error");
        return;
    }
    // ---- CHI CHEN THEM (YOUTUBE): kiem tra da co nguon hop le chua ----
    if (currentSourceType === "local" && !currentVideoFilename) {
        setMsg(sessionMsg, "Vui lòng chọn một video hoặc nhập link YouTube.", "error");
        return;
    }
    if (currentSourceType === "youtube" && !currentYoutubeUrl) {
        setMsg(sessionMsg, "Vui lòng xác nhận link YouTube trước khi bắt đầu.", "error");
        return;
    }
    const payload = {
        video_filename: currentSourceType === "local" ? currentVideoFilename : "",
        // ---- CHI CHEN THEM (YOUTUBE) ----
        source_type: currentSourceType,
        youtube_url: currentSourceType === "youtube" ? currentYoutubeUrl : "",
        x1: point1.x, y1: point1.y,
        x2: point2.x, y2: point2.y,
        frame_width: naturalWidth, frame_height: naturalHeight,
        huong_1_label: huong1Input.value.trim(),
        huong_2_label: huong2Input.value.trim(),
    };
    try {
        const saveRes = await fetch("/api/config/crossline", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const saveData = await saveRes.json();
        if (!saveData.ok) {
            setMsg(sessionMsg, saveData.message || "Lỗi khi lưu cấu hình.", "error");
            return;
        }
        const startRes = await fetch("/api/session/start", { method: "POST" });
        const startData = await startRes.json();
        if (!startData.ok) {
            setMsg(sessionMsg, startData.message || "Không thể bắt đầu phiên.", "error");
            return;
        }
        huong1Header.textContent = huong1Input.value.trim();
        huong2Header.textContent = huong2Input.value.trim();
        applyLockState(true);
        setPausedUI(false);
        setMsg(sessionMsg, startData.message, "success");
        await syncDbSelectorFromStatus();
        startVideoFramePolling();
    } catch (e) {
        setMsg(sessionMsg, "Lỗi kết nối máy chủ.", "error");
    }
});
btnDung.addEventListener("click", async () => {
    try {
        const res = await fetch("/api/session/stop", { method: "POST" });
        const data = await res.json();
        stopVideoFramePolling();
        applyLockState(false);
        setMsg(sessionMsg, data.message || "Đã dừng.", data.ok ? "" : "error");
        // ---- CHI CHEN THEM: dat lai o FPS ve "--" khi Dung ----
        fpsValueEl.textContent = "-- FPS";
        if (data.ok) {
            await syncDbSelectorFromStatus();
        }
    } catch (e) {
        setMsg(sessionMsg, "Lỗi kết nối máy chủ khi dừng.", "error");
    }
});
function applyLockState(locked) {
    crosslineLocked = locked;
    videoSelect.disabled = locked;
    // ---- CHI CHEN THEM (YOUTUBE): khoa ca o nhap link + nut xac nhan ----
    youtubeUrlInput.disabled = locked;
    btnConfirmYoutube.disabled = locked;
    dbSelect.disabled = locked;
    btnPickStart.disabled = locked;
    btnPickEnd.disabled = locked;
    coordStart.readOnly = locked || point1Locked;
    coordEnd.readOnly = locked;
    huong1Input.readOnly = locked;
    huong2Input.readOnly = locked;
    btnBatDau.disabled = locked;
    btnDung.disabled = !locked;
    btnTamDung.disabled = !locked;
    btnPickStart.classList.remove("picking");
    btnPickEnd.classList.remove("picking");
    pickingMode = null;
    if (!locked) {
        setPausedUI(false);
    }
    updateDbDisconnectButtonState();
    redrawOverlay();
}

// ============================================================
// 5. TAM DUNG / TIEP TUC
// ============================================================
function startStatsPolling() {
    if (statsPollHandle) return;
    fetchLiveStats();
    statsPollHandle = setInterval(fetchLiveStats, 5000);
}
function stopStatsPolling() {
    if (statsPollHandle) {
        clearInterval(statsPollHandle);
        statsPollHandle = null;
    }
}
// ------------------------------------------------------------
// POLLING KHUNG HINH THAT dang duoc xu ly (thay the anh tinh
// frame dau tien). Cross-Line (duong do/cham vang/nhan goc) van
// do overlay canvas o client tu ve de len tren - server CHI ve
// bounding box cua tung phuong tien (xem services/video_worker.py).
// ------------------------------------------------------------
function startVideoFramePolling() {
    if (videoFramePollHandle) return;
    fetchLiveVideoFrame();
    videoFramePollHandle = setInterval(fetchLiveVideoFrame, 40);
}
function stopVideoFramePolling() {
    if (videoFramePollHandle) {
        clearInterval(videoFramePollHandle);
        videoFramePollHandle = null;
    }
}
async function fetchLiveVideoFrame() {
    try {
        const res = await fetch("/api/video/live_frame");
        const data = await res.json();
        if (!data.ok) {
            stopVideoFramePolling();
            applyLockState(false);
            await syncDbSelectorFromStatus();
            setMsg(sessionMsg, data.message || "Đã dừng do lỗi xử lý video.", "error");
            // ---- CHI CHEN THEM: dat lai o FPS khi co loi ----
            fpsValueEl.textContent = "-- FPS";
            return;
        }
        if (data.image_base64) {
            frameImage.src = data.image_base64;
        }
        // ---- CHI CHEN THEM: cap nhat o hien thi FPS moi lan poll ----
        if (typeof data.current_fps === "number") {
            fpsValueEl.textContent = data.current_fps.toFixed(1) + " FPS";
        }
        if (data.video_ended) {
            stopVideoFramePolling();
            applyLockState(false);
            await syncDbSelectorFromStatus();
            setMsg(sessionMsg, data.message || "Video đã phát hết.", "success");
            // ---- CHI CHEN THEM: dat lai o FPS khi video ket thuc ----
            fpsValueEl.textContent = "-- FPS";
        }
    } catch (e) {
        // Loi mang tam thoi - khong dung han phien, se tu thu lai o
        // lan poll ke tiep.
    }
}
function setPausedUI(paused) {
    isPaused = paused;
    btnTamDung.textContent = paused ? "Tiếp tục" : "Tạm dừng";
    if (paused) {
        stopStatsPolling();
    } else {
        startStatsPolling();
    }
}
btnTamDung.addEventListener("click", async () => {
    const endpoint = isPaused ? "/api/session/resume" : "/api/session/pause";
    try {
        const res = await fetch(endpoint, { method: "POST" });
        const data = await res.json();
        if (!data.ok) {
            setMsg(sessionMsg, data.message || "Lỗi.", "error");
            return;
        }
        setPausedUI(!isPaused);
        setMsg(sessionMsg, data.message, "success");
    } catch (e) {
        setMsg(sessionMsg, "Lỗi kết nối máy chủ.", "error");
    }
});

// ============================================================
// 6. THONG KE CONG DON
// ============================================================
async function fetchLiveStats() {
    try {
        const res = await fetch("/api/stats/live");
        const data = await res.json();
        setServerTimeAnchor(data.current_server_time);
        if (!data.ok) {
            statsHint.textContent = data.message || "";
            return;
        }
        statsHint.textContent = "";
        if (data.huong_1_label) huong1Header.textContent = data.huong_1_label;
        if (data.huong_2_label) huong2Header.textContent = data.huong_2_label;
        data.counts.forEach(row => {
            const ids = CLASS_KEY_TO_INPUT[row.class_key];
            if (!ids) return;
            document.getElementById(ids.h1).value = row.huong_1;
            document.getElementById(ids.h2).value = row.huong_2;
        });
    } catch (e) {
        statsHint.textContent = "Lỗi khi tải thống kê.";
    }
}

// ============================================================
// 7. XUAT DU LIEU CHI TIET (POPUP)
// ============================================================
function updateExportButtonState() {
    const tu = tuThoiDiemInput.value;
    const den = denThoiDiemInput.value;
    btnExportDetail.disabled = !(tu && den);
}
tuThoiDiemInput.addEventListener("change", updateExportButtonState);
denThoiDiemInput.addEventListener("change", updateExportButtonState);
btnExportDetail.addEventListener("click", async () => {
    const tu = tuThoiDiemInput.value;
    const den = denThoiDiemInput.value;
    if (!tu || !den) return;
    const params = new URLSearchParams({ tu_thoi_diem: tu, den_thoi_diem: den });
    try {
        const res = await fetch("/api/query_detail?" + params.toString());
        const data = await res.json();
        if (!data.ok) {
            alert(data.message || "Lỗi khi truy vấn dữ liệu.");
            return;
        }
        detailRangeInfo.textContent =
            `Khoảng thời gian: ${formatDateVN(data.effective_start)} → ${formatDateVN(data.effective_end)} ` +
            `(tổng cộng ${data.total_events} lượt cắt vạch)`;
        detailSummaryTable.innerHTML = "";
        data.summary.forEach(row => {
            const tr = document.createElement("tr");
            [row.class_name, row.direction, row.count].forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                tr.appendChild(td);
            });
            detailSummaryTable.appendChild(tr);
        });
        detailListTable.innerHTML = "";
        data.detail.forEach(row => {
            const tr = document.createElement("tr");
            // ---- CHI CHEN THEM: hien thi them cot fps_tai_thoi_diem ----
            const fpsDisplay = (row.fps_tai_thoi_diem !== null && row.fps_tai_thoi_diem !== undefined)
                ? row.fps_tai_thoi_diem.toFixed(1)
                : "-";
            [formatDateVN(row.timestamp), row.track_id, row.class_name, row.direction, fpsDisplay].forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                tr.appendChild(td);
            });
            detailListTable.appendChild(tr);
        });
        detailModal.classList.remove("hidden");
    } catch (e) {
        alert("Lỗi kết nối máy chủ khi truy vấn dữ liệu.");
    }
});
btnDownloadCsv.addEventListener("click", () => {
    const tu = tuThoiDiemInput.value;
    const den = denThoiDiemInput.value;
    const params = new URLSearchParams({ tu_thoi_diem: tu, den_thoi_diem: den });
    window.location.href = "/api/query_detail/export_csv?" + params.toString();
});
btnCloseDetailModal.addEventListener("click", () => {
    detailModal.classList.add("hidden");
});

// ============================================================
// KHOI TAO
// ============================================================
async function loadExistingCrosslineConfig() {
    try {
        const res = await fetch("/api/config/crossline");
        const cfg = await res.json();
        if (cfg.x1 !== null && cfg.x1 !== undefined) {
            point1 = { x: cfg.x1, y: cfg.y1 };
            point2 = { x: cfg.x2, y: cfg.y2 };
            point1Locked = true;
            coordStart.value = `${cfg.x1}, ${cfg.y1}`;
            coordEnd.value = `${cfg.x2}, ${cfg.y2}`;
            coordStart.readOnly = true;
            huong1Input.value = cfg.huong_1_label || "";
            huong2Input.value = cfg.huong_2_label || "";
            huong1Header.textContent = cfg.huong_1_label || "Hướng 1";
            huong2Header.textContent = cfg.huong_2_label || "Hướng 2";
            redrawOverlay();
        }
    } catch (e) { /* bo qua */ }
}
async function loadExistingSessionState() {
    try {
        const res = await fetch("/api/session/status");
        const data = await res.json();
        if (data.dang_chay) {
            await loadExistingCrosslineConfig();
            applyLockState(true);
            setPausedUI(!!data.tam_dung);
            startVideoFramePolling();
        }
    } catch (e) { /* bo qua */ }
}
(function init() {
    loadVideoList();
    loadDbList().then(() => {
        syncDbSelectorFromStatus();
    });
    loadExistingSessionState();
    startStatsPolling();
})();
