// 15 pertanyaan kuesioner
const PERTANYAAN = [
    "Saya tertarik mempelajari pengelolaan sistem informasi",
    "Saya tertarik mempelajari audit sistem informasi",
    "Saya tertarik menerapkan teknologi untuk menunjang bisnis",
    "Saya mampu melakukan analisis penerapan sistem",
    "Saya mampu membangun sistem informasi",
    "Saya mampu mengelola bisnis berbasis teknologi",
    "Saya senang memecahkan masalah kompleks",
    "Saya senang mempelajari algoritma dan logika",
    "Saya tertarik dengan perkembangan teknologi terbaru",
    "Saya mengikuti perkembangan AI dan machine learning",
    "Saya memiliki pengalaman mengerjakan proyek pemrograman",
    "Saya memiliki pengalaman mengerjakan proyek jaringan",
    "Saya ingin berkarir di bidang pengembangan perangkat lunak",
    "Saya ingin berkarir di bidang kecerdasan artifisial",
    "Saya ingin berkarir di bidang jaringan komputer"
];

const SKALA = [
    { nilai: 1, label: "Sangat Tidak Sesuai" },
    { nilai: 2, label: "Tidak Sesuai" },
    { nilai: 3, label: "Cukup" },
    { nilai: 4, label: "Sesuai" },
    { nilai: 5, label: "Sangat Sesuai" }
];

const jawaban = new Array(15).fill(null);
const container = document.getElementById("pertanyaan-container");

// Render pertanyaan
PERTANYAAN.forEach((teks, i) => {
    const div = document.createElement("div");
    div.className = "pertanyaan-card";
    div.innerHTML = `
        <p><strong>${i + 1}.</strong> ${teks}</p>
        <div class="skala">
            ${SKALA.map(s => `
                <label>
                    <input type="radio" name="q${i}" value="${s.nilai}"
                        onchange="setJawaban(${i}, ${s.nilai})">
                    <span>${s.nilai} — ${s.label}</span>
                </label>
            `).join("")}
        </div>
    `;
    container.appendChild(div);
});

function setJawaban(index, nilai) {
    jawaban[index] = nilai;
    updateProgress();
}

function updateProgress() {
    const terjawab = jawaban.filter(j => j !== null).length;
    document.getElementById("progress").style.width = (terjawab / 15 * 100) + "%";
    document.getElementById("progress-text").textContent = `${terjawab} / 15 terjawab`;
    document.getElementById("btn-submit").disabled = terjawab !== 15;
}

// Submit
document.getElementById("form-kuesioner").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nama = document.getElementById("nama").value || "Anonim";

    const btn = document.getElementById("btn-submit");
    btn.disabled = true;
    btn.textContent = "Menghitung...";

    try {
        const response = await fetch("/api/rekomendasi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nama, jawaban })
        });

        const hasil = await response.json();
        sessionStorage.setItem("hasil", JSON.stringify(hasil));
        window.location.href = "/hasil";
    } catch (err) {
        alert("Terjadi kesalahan: " + err.message);
        btn.disabled = false;
        btn.textContent = "Lihat Hasil Rekomendasi";
    }
});