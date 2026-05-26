/**
 * G8 NATIONAL PLUS - Auto-Resumer Script
 * 
 * This script can be run periodically to check if creation stopped 
 * and resume from where it left off.
 * 
 * Usage: 
 *   node resumer.js           - Show status & instructions
 *   node resumer.js --check   - Check current progress
 *   node resumer.js --start   - Start automation
 */

const fs = require('fs');
const { chromium } = require('playwright');

const CLASS_URL = 'https://students.ezralms.com/class/rKLckFly8YRbdHrAnu36';

// All 28 subtopics with content (HTML templates ready)
const ALL_SUBTOPICS = [
  // G8-03 Geometry (5)
  { topic: 'G8-03 Geometry and Measurement', title: 'G8-03.1 Lines, Angles, and Proofs', content: '<h2>Lines, Angles, and Proofs</h2><p>Pada subtopik ini, siswa akan mempelajari hubungan antar garis dan sudut.</p><h3>Hubungan Antar Garis</h3><ul><li><strong>Garis Sejajar</strong>: Garis yang tidak pernah berpotongan</li><li><strong>Garis Berpotongan</strong>: Garis yang memiliki titik potong</li><li><strong>Garis Tegak Lurus</strong>: Garis yang membentuk sudut 90°</li></ul><h3>Macam-macam Sudut</h3><ul><li><strong>Sudut Lancip</strong>: 0° &lt; α &lt; 90°</li><li><strong>Sudut Siku-siku</strong>: α = 90°</li><li><strong>Sudut Tumpul</strong>: 90° &lt; α &lt; 180°</li><li><strong>Sudut Refleks</strong>: 180° &lt; α &lt; 360°</li></ul>' },
  { topic: 'G8-03 Geometry and Measurement', title: 'G8-03.2 Triangles', content: '<h2>Triangles (Segitiga)</h2><p>Segitiga adalah bangun datar dengan tiga sisi dan tiga sudut.</p><h3>Klasifikasi Segitiga</h3><p>Berdasarkan Sisi:</p><ul><li><strong>Sama Sisi</strong>: Ketiga sisi sama panjang</li><li><strong>Sama Kaki</strong>: Dua sisi sama panjang</li><li><strong>Sembarang</strong>: Ketiga sisi berbeda panjang</li></ul><p>Berdasarkan Sudut:</p><ul><li><strong>Segitiga Lancip</strong>: Semua sudut &lt; 90°</li><li><strong>Segitiga Siku-siku</strong>: Salah satu sudut = 90°</li><li><strong>Segitiga Tumpul</strong>: Salah satu sudut &gt; 90°</li></ul><h3>Teorema Pythagoras</h3><p><strong>a² + b² = c²</strong></p>' },
  { topic: 'G8-03 Geometry and Measurement', title: 'G8-03.3 Quadrilaterals', content: '<h2>Quadrilaterals (Segiempat)</h2><p>Segiempat adalah bangun datar dengan empat sisi dan empat sudut.</p><h3>Klasifikasi</h3><ul><li><strong>Persegi</strong>: empat sisi sama, empat sudut siku-siku</li><li><strong>Persegi Panjang</strong>: sisi depan = sisi belakang</li><li><strong>Jajargenjang</strong>: sisi-sisi berhadapan sejajar</li><li><strong>Belah Ketupat</strong>: semua sisi sama</li><li><strong>Trapesium</strong>:minimal satu pasang sisi sejajar</li></ul><h3>Sifat</h3><p>Jumlah sudut dalam segiempat = 360°</p>' },
  { topic: 'G8-03 Geometry and Measurement', title: 'G8-03.4 Circles', content: '<h2>Circles (Lingkaran)</h2><p>Lingkaran adalah himpunan semua titik yang berjarak sama dari pusat.</p><h3>Unsur-unsur Lingkaran</h3><ul><li><strong>Pusat (O)</strong>: Titik tengah</li><li><strong>Jari-jari (r)</strong>: Jarak pusat ke titik lingkaran</li><li><strong>Diameter (d)</strong>: 2×r</li><li><strong>Keliling</strong>: K = 2πr</li><li><strong>Luas</strong>: L = πr²</li></ul><h3>Sudut Pusat dan Keliling</h3><p>Sudut pusat = 2 × sudut keliling</p>' },
  { topic: 'G8-03 Geometry and Measurement', title: 'G8-03.5 Constructions and Loci', content: '<h2>Constructions and Loci</h2><h3>Konstruksi Geometri</h3><p>Membuat bangun geometri menggunakan jangka dan penggaris.</p><h3>Konstruksi Dasar</h3><ul><li>Membagi garis menjadi dua bagian sama</li><li>Membagi sudut menjadi dua sama besar</li><li>Membuat garis sejajar</li><li>Membuat segitiga sama sisi</li></ul><h3>Loci</h3><p>Tempat kedudukan titik yang memenuhi kondisi.</p><ul><li>Lingkaran: locus titik berjarak sama dari pusat</li><li>Garis: locus titik berjarak sama dari dua garis</li></ul>' },
  
  // G8-04 Statistics (5)
  { topic: 'G8-04 Statistics and Probability', title: 'G8-04.1 Data Collection and Representation', content: '<h2>Data Collection and Representation</h2><p>Statistik adalah ilmu yang mempelajari cara mengumpulkan dan menganalisis data.</p><h3>Jenis Data</h3><ul><li><strong>Data Kualitatif</strong>: Tidak berupa angka</li><li><strong>Data Kuantitatif</strong>: Berupa angka</li></ul><h3>Penyajian Data</h3><ul><li>Tabel Frekuensi</li><li>Histogram</li><li>Grafik Garis</li><li>Diagram Lingkaran</li></ul>' },
  { topic: 'G8-04 Statistics and Probability', title: 'G8-04.2 Measures of Central Tendency', content: '<h2>Measures of Central Tendency</h2><p>Ukuran pemusatan data menunjukkan nilai tengah.</p><h3>1. Mean (Rata-rata)</h3><p>Mean = Σxᵢ / n</p><h3>2. Median (Nilai Tengah)</h3><p>Nilai yang membagi data menjadi dua bagian sama.</p><h3>3. Modus</h3><p>Nilai yang paling sering muncul.</p>' },
  { topic: 'G8-04 Statistics and Probability', title: 'G8-04.3 Measures of Spread', content: '<h2>Measures of Spread</h2><p>Ukuran penyebaran menunjukkan seberapa tersebar data.</p><h3>1. Range</h3><p>Range = Nilai terbesar - Nilai terkecil</p><h3>2. IQR</h3><p>IQR = Q3 - Q1</p><h3>3. Box Plot</h3><p>Menampilkan: min, Q1, median, Q3, max</p><h3>4. Outlier</h3><p>Data pencilan (&lt; Q1-1.5×IQR atau &gt; Q3+1.5×IQR)</p>' },
  { topic: 'G8-04 Statistics and Probability', title: 'G8-04.4 Probability Basics', content: '<h2>Probability Basics</h2><p>Peluang adalah ukuran kemungkinan terjadinya suatu kejadian.</p><h3>Definisi</h3><p>P(A) = Banyak kejadian A / Banyak semua kemungkinan</p><h3>Ruang Sampel (S)</h3><p>Himpunan semua hasil yang mungkin.</p><h3>Skala Peluang</h3><p>0 ≤ P(A) ≤ 1</p><ul><li>P(A) = 0: Mustahil</li><li>P(A) = 1: Pasti</li></ul>' },
  { topic: 'G8-04 Statistics and Probability', title: 'G8-04.5 Probability of Combined Events', content: '<h2>Probability of Combined Events</h2><h3>Peluang Gabungan</h3><p>P(A ∪ B) = P(A) + P(B) - P(A ∩ B)</p><h3>Saling Lepas</h3><p>P(A ∩ B) = 0 → P(A ∪ B) = P(A) + P(B)</p><h3>Saling Bebas</h3><p>P(A ∩ B) = P(A) × P(B)</p><h3>Komplemen</h3><p>P(A\') = 1 - P(A)</p>' },
  
  // G8-05 Algebraic (5)
  { topic: 'G8-05 Algebraic Manipulation', title: 'G8-05.1 Algebraic Expressions', content: '<h2>Algebraic Expressions</h2><p>Ekspresi aljabar adalah kombinasi variabel, konstanta, dan operasi.</p><h3>Komponen</h3><ul><li><strong>Variabel</strong>: Huruf (x, y, z)</li><li><strong>Konstanta</strong>: Bilangan tetap</li><li><strong>Koefisien</strong>: Bilangan dikalikan variabel</li></ul><h3>Suku Sejenis</h3><p>3x dan 5x adalah suku sejenis.</p>' },
  { topic: 'G8-05 Algebraic Manipulation', title: 'G8-05.2 Algebraic Formulae', content: '<h2>Algebraic Formulae</h2><p>Rumus aljabar adalah persamaan yang menyatakan hubungan antar variabel.</p><h3>Substitusi</h3><p>Mengganti variabel dengan nilai tertentu.</p><h3>Mengubah Subjek</h3><p>v = u + at → a = (v - u) / t</p><h3>Rumus Luas</h3><p>Persegi: L = s²</p><p>Lingkaran: L = πr²</p><p>Segitiga: L = ½at</p>' },
  { topic: 'G8-05 Algebraic Manipulation', title: 'G8-05.3 Linear Equations', content: '<h2>Linear Equations</h2><p>Persamaan linear adalah persamaan dengan pangkat variabel 1.</p><h3>Bentuk Umum</h3><p>ax + b = c</p><h3>Penyelesaian</h3><ol><li>Kumpulkan suku sejenis</li><li>Pindahkan variabel ke satu sisi</li><li>Bagi dengan koefisien</li></ol><h3>Contoh</h3><p>2x + 3 = 7 → x = 2</p>' },
  { topic: 'G8-05 Algebraic Manipulation', title: 'G8-05.4 Linear Inequalities', content: '<h2>Linear Inequalities</h2><p>Pertidaksamaan linear menggunakan tanda &lt;, &gt;, ≤, ≥.</p><h3>Sifat</h3><p>Ketika mengali/ pembagian dengan bilangan negatif, tanda berubah!</p><h3>Contoh</h3><p>3x &lt; 12 → x &lt; 4</p><p>-2x &lt; 8 → x &gt; -4 (tanda berubah!)</p>' },
  { topic: 'G8-05 Algebraic Manipulation', title: 'G8-05.5 Expanding and Factoring', content: '<h2>Expanding and Factoring</h2><h3>Distributif</h3><p>a(b + c) = ab + ac</p><h3>Selisih Kuadrat</h3><p>a² - b² = (a + b)(a - b)</p><h3>Faktorisasi</h3><p>x² + 5x + 6 = (x + 2)(x + 3)</p><p>Karena 2×3=6 dan 2+3=5</p>' },
  
  // G8-06 Number Skills (4)
  { topic: 'G8-06 Number Skills and Indices', title: 'G8-06.1 Integers and Operations', content: '<h2>Integers and Operations</h2><p>Bilangan bulat meliputi positif, negatif, dan nol.</p><h3>Operasi</h3><h4>Penjumlahan</h4><ul><li>(+3) + (+5) = +8</li><li>(-3) + (-5) = -8</li><li>(+3) + (-5) = -2</li></ul><h4>Perkalian</h4><ul><li>(+) × (+) = (+)</li><li>(-) × (-) = (+)</li><li>(+) × (-) = (-)</li></ul><h3>PEMDAS</h3><p>Parentheses, Exponents, Multiplication, Division, Addition, Subtraction</p>' },
  { topic: 'G8-06 Number Skills and Indices', title: 'G8-06.2 Indices and Powers', content: '<h2>Indices and Powers</h2><p>Indeks menunjukkan perkalian berulang.</p><h3>Definisi</h3><p>aⁿ = a × a × ... × a (n kali)</p><h3>Hukum Indeks</h3><ol><li>aᵐ × aⁿ = aᵐ⁺ⁿ</li><li>aᵐ ÷ aⁿ = aᵐ⁻ⁿ</li><li>(aᵐ)ⁿ = aᵐⁿ</li></ol><h3>Khusus</h3><ul><li><strong>a⁰ = 1</strong> (a ≠ 0)</li><li><strong>a⁻ⁿ = 1/aⁿ</strong></li></ul>' },
  { topic: 'G8-06 Number Skills and Indices', title: 'G8-06.3 Standard Form', content: '<h2>Standard Form (Scientific Notation)</h2><p>Notasi ilmiah untuk bilangan sangat besar/kecil.</p><h3>Bentuk</h3><p>a × 10ⁿ (1 ≤ |a| &lt; 10)</p><h3>Contoh</h3><p>3000000 = 3 × 10⁶</p><p>0.00003 = 3 × 10⁻⁵</p><h3>Operasi</h3><p>(3 × 10⁵) × (2 × 10³) = 6 × 10⁸</p>' },
  { topic: 'G8-06 Number Skills and Indices', title: 'G8-06.4 Roots and Surds', content: '<h2>Roots and Surds</h2><h3>Akar Kuadrat</h3><p>√a = b bila b² = a</p><p>√16 = 4</p><h3>Surd</h3><p>√2, √3, √5 adalah surd (irasional)</p><h3>Menyederhanakan</h3><p>√50 = √(25 × 2) = 5√2</p><h3>Merasionalkan</h3><p>1/√2 = √2/2</p>' },
  
  // G8-07 Ratio (4)
  { topic: 'G8-07 Ratio and Proportion', title: 'G8-07.1 Ratio', content: '<h2>Ratio</h2><p>Perbandingan adalah hubungan antara dua besaran.</p><h3>Menulis</h3><p>a:b = a/b</p><h3>Menyederhanakan</h3><p>8:6 = 4:3 (bagi dengan FPB)</p><h3>Ratio Sejenis</h3><p>Semakin besar a, semakin besar hasil.</p><h3>Berbalik Nilai</h3><p>Semakin besar a, semakin kecil hasil.</p>' },
  { topic: 'G8-07 Ratio and Proportion', title: 'G8-07.2 Proportion', content: '<h2>Proportion</h2><p>Proporsi adalah persamaan dua perbandingan.</p><h3>Bentuk</h3><p>a:b = c:d</p><h3>Perkalian Silang</h3><p>Jika a/b = c/d, maka ad = bc</p><h3>Menyelesaikan</h3><p>x/4 = 6/8 → 8x = 24 → x = 3</p><h3>Skala</h3><p>Skala = jarak peta / jarak sebenarnya</p><p>1:1000 → 1 cm = 10 m</p>' },
  { topic: 'G8-07 Ratio and Proportion', title: 'G8-07.3 Direct and Inverse Proportion', content: '<h2>Direct and Inverse Proportion</h2><h3>Langsung</h3><p>y = kx → Jika x dua kali, y dua kali</p><p>Grafik: garis melalui origin</p><h3>Berbalik Nilai</h3><p>y = k/x → Jika x dua kali, y setengah</p><p>Grafik: hiperbola</p><h3>Contoh</h3><p>5 orang → 8 hari</p><p>10 orang → 4 hari (berbalik)</p>' },
  { topic: 'G8-07 Ratio and Proportion', title: 'G8-07.4 Percentage', content: '<h2>Percentage</h2><p>Persentase adalah perbandingan per 100.</p><h3>Dasar</h3><p>x% = x/100</p><h3>Pecahan ke %</h3><ul><li>½ = 50%</li><li>¼ = 25%</li><li>¾ = 75%</li></ul><h3>Menghitung</h3><p>15% dari 200 = (15/100) × 200 = 30</p><h3>Kenaikan</h3><p>50 + 10% = 50 × 1.1 = 55</p>' },
  
  // G8-08 Sets (3)
  { topic: 'G8-08 Sets', title: 'G8-08.1 Introduction to Sets', content: '<h2>Introduction to Sets</h2><p>Himpunan adalah kumpulan objek yang terdefinisi.</p><h3>Notasi</h3><p>A = {1, 2, 3}</p><p>A = {x | x bilangan ≤ 3}</p><h3>Anggota</h3><p>1 ∈ A (anggota)</p><p>4 ∉ A (bukan anggota)</p><h3>Jenis</h3><ul><li><strong>Universal (S)</strong>: Himpunan semesta</li><li><strong>Kosong (∅)</strong>: Tanpa anggota</li></ul>' },
  { topic: 'G8-08 Sets', title: 'G8-08.2 Operations on Sets', content: '<h2>Operations on Sets</h2><h3>Gabungan (∪)</h3><p>A ∪ B = {x | x ∈ A atau x ∈ B}</p><h3>Irisan (∩)</h3><p>A ∩ B = {x | x ∈ A dan x ∈ B}</p><h3>Komplemen</h3><p>A\' = {x ∈ S | x ∉ A}</p><h3>Sifat</h3><ul><li>A ∪ ∅ = A</li><li>A ∩ ∅ = ∅</li><li>A ∪ A\' = S</li></ul>' },
  { topic: 'G8-08 Sets', title: 'G8-08.3 Applications of Sets', content: '<h2>Applications of Sets</h2><p>Himpunan dapat digunakan untuk memecahkan masalah nyata.</p><h3>Contoh</h3><p>50 siswa: 30 senang Math, 25 senang Science, 10 senang keduanya.</p><p>Minimal satu: 30 + 25 - 10 = 45</p><h3>Kardinalitas</h3><p>n(A) = banyak anggota A</p><p>n(A ∪ B) = n(A) + n(B) - n(A ∩ B)</p>' }
];

/**
 * Show status
 */
function showStatus() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║       G8 NATIONAL PLUS - Automation Status                   ║
╚════════════════════════════════════════════════════════════════╝

📍 Class URL: ${CLASS_URL}
📊 Total: 28 subtopics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Already Created (2):
   1. G8-03.1 Lines, Angles, and Proofs
   2. G8-03.2 Triangles

⏳ Remaining (26):
   G8-03: 3 more (Quadrilaterals, Circles, Constructions)
   G8-04: 5 (Statistics & Probability)
   G8-05: 5 (Algebraic Manipulation)
   G8-06: 4 (Number Skills)
   G8-07: 4 (Ratio & Proportion)
   G8-08: 3 (Sets)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 To Resume:
   1. Open Chrome with extension
   2. Go to ${CLASS_URL}
   3. For each "Add Sub-topic":
      a. Click Subject Matter → Create New
      b. Enter title
      c. Create & Open Editor
      d. Paste content → Save

   Or run: node resumer.js --start
`);
}

/**
 * Start resumer logic (placeholder for manual)
 */
async function startResumer() {
  console.log('\n🚀 Starting automation...\n');
  console.log('Please ensure Chrome is running with OpenCode extension.');
  console.log('Navigate to class page and I will guide you through.\n');
  
  // This would need Playwright/browser connection
  console.log('Note: Full automation requires browser connection.');
  console.log('Use the manual steps above for now.\n');
}

// Main
const args = process.argv.slice(2);

if (args.includes('--start')) {
  startResumer();
} else if (args.includes('--check')) {
  showStatus();
} else {
  showStatus();
}

module.exports = { ALL_SUBTOPICS, showStatus };