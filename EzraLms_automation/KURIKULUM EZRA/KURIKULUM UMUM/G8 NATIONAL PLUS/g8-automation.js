/**
 * G8 NATIONAL PLUS - Automated Content Creator
 * 
 * This script automates adding all subtopics to the G8 NATIONAL PLUS class on EzraLMS.
 * It reads from the curriculum plan and creates topics + subject matter.
 * 
 * Usage: node g8-automation.js
 * 
 * Prerequisites:
 * - Chrome should be running with OpenCode Browser extension
 * - Login credentials ready
 */

const fs = require('fs');
const path = require('path');

// Configuration
const CLASS_URL = 'https://students.ezralms.com/class/rKLckFly8YRbdHrAnu36';
const USERNAME = 'EzraT';
const PIN = '223183';

// Curriculum data - all topics to be created
const CURRICULUM = [
  {
    topic: 'G8-03 Geometry and Measurement',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-03.1 Lines, Angles, and Proofs',
        content: `<h2>Lines, Angles, and Proofs</h2>
<p>Pada subtopik ini, siswa akan mempelajari hubungan antar garis dan sudut serta membuktikan konsep geometri menggunakan penalaran logis.</p>
<h3>Hubungan Antar Garis</h3>
<ul>
<li><strong>Garis Sejajar</strong>: Garis yang tidak pernah berpotongan</li>
<li><strong>Garis Berpotongan</strong>: Garis yang memiliki titik potong</li>
<li><strong>Garis Tegak Lurus</strong>: Garis yang membentuk sudut 90°</li>
</ul>
<h3>Macam-macam Sudut</h3>
<ul>
<li><strong>Sudut Lancip</strong>: 0° &lt; α &lt; 90°</li>
<li><strong>Sudut Siku-siku</strong>: α = 90°</li>
<li><strong>Sudut Tumpul</strong>: 90° &lt; α &lt; 180°</li>
<li><strong>Sudut Refleks</strong>: 180° &lt; α &lt; 360°</li>
</ul>
<h3>Sifat Sudut</h3>
<p>Jumlah sudut pada garis lurus adalah 180°.</p>
<p>Dua sudut yang berpelurus jumlahnya 180°.</p>
<p>Dua sudut yang bertolak belakang sama besar.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-03.2 Triangles',
        content: `<h2>Triangles (Segitiga)</h2>
<p>Segitiga adalah bangun datar dengan tiga sisi dan tiga sudut.</p>
<h3>Klasifikasi Segitiga</h3>
<p>Berdasarkan Sisi:</p>
<ul>
<li><strong>Sama Sisi</strong>: Ketiga sisi sama panjang (60° setiap sudut)</li>
<li><strong>Sama Kaki</strong>: Dua sisi sama panjang</li>
<li><strong>Sembarang</strong>: Ketiga sisi berbeda panjang</li>
</ul>
<p>Berdasarkan Sudut:</p>
<ul>
<li><strong>Segitiga Lancip</strong>: Semua sudut &lt; 90°</li>
<li><strong>Segitiga Siku-siku</strong>: Salah satu sudut = 90°</li>
<li><strong>Segitiga Tumpul</strong>: Salah satu sudut &gt; 90°</li>
</ul>
<h3>Teorema Pythagoras</h3>
<p>Untuk segitiga siku-siku:</p>
<p><strong>a² + b² = c²</strong></p>
<p>Di mana c adalah sisi miring (hypotenuse).</p>
<h3>Ketaksamaan Segitiga</h3>
<p>Jumlah dua sisi selalu lebih besar dari sisi ketiga.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-03.3 Quadrilaterals',
        content: `<h2>Quadrilaterals (Segiempat)</h2>
<p>Segiempat adalah bangun datar dengan empat sisi dan empat sudut.</p>
<h3>Klasifikasi Segiempat</h3>
<ul>
<li><strong>Persegi</strong>:empat sisi sama, empat sudut siku-siku</li>
<li><strong>Persegi Panjang</strong>: sisi depan = sisi belakang, sisi kiri = kanan</li>
<li><strong>Jajargenjang</strong>: sisi-sisi berhadapan sejajar</li>
<li><strong>Belah Ketupat</strong>: semua sisi sama, sisi sejajar</li>
<li><strong>Layang-layang</strong>: dua pasang sisi berdekatan sama</li>
<li><strong>Trapesium</strong>:minimal satu pasang sisi sejajar</li>
</ul>
<h3>Sifat-sifat</h3>
<p>Jumlah sudut dalam segiempat = 360°</p>
<p>Persegi: semua sisi sama, semua sudut 90°</p>
<p>Jajargenjang: sisi sejajar sama panjang</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-03.4 Circles',
        content: `<h2>Circles (Lingkaran)</h2>
<p>Lingkaran adalah himpunan semua titik yang berjarak sama dari pusat.</p>
<h3>Unsur-unsur Lingkaran</h3>
<ul>
<li><strong>Pusat (O)</strong>: Titik tengah lingkaran</li>
<li><strong>Jari-jari (r)</strong>: Jarak pusat ke titik lingkaran</li>
<li><strong>Diameter (d)</strong>: 2×r, garis melalui pusat</li>
<li><strong>Busur</strong>: Bagian dari keliling lingkaran</li>
<li><strong>Tali Busur</strong>: Garis menghubungkan dua titik pada lingkaran</li>
<li><strong>Juring</strong>: Daerah yang dibatasi dua jari-jari</li>
<li><strong>Tembereng</strong>: Daerah yang dibatasi tali busur dan busur</li>
</ul>
<h3>Rumus Lingkaran</h3>
<p><strong>Keliling</strong>: K = 2πr = πd</p>
<p><strong>Luas</strong>: L = πr²</p>
<h3>Sudut Pusat dan Sudut Keliling</h3>
<p>Sudut pusat = 2 × sudut keliling yang menghadap busur sama.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-03.5 Constructions and Loci',
        content: `<h2>Constructions and Loci</h2>
<h3>Konstruksi Geometri</h3>
<p>Konstruksi adalah cara membuat bangun geometri menggunakan jangka dan penggaris.</p>
<h3>Konstruksi Dasar</h3>
<ul>
<li>Membagi garis menjadi dua bagian sama</li>
<li>Membagi sudut menjadi dua sama besar</li>
<li>Membuat garis sejajar melalui titik</li>
<li>Membuat segitiga sama sisi</li>
</ul>
<h3>Loci (Tempat Kedudukan)</h3>
<p>Loci adalah himpunan semua titik yang memenuhi kondisi tertentu.</p>
<p>Contoh:</p>
<ul>
<li>Lingkaran: locus titik dengan jarak sama dari titik pusat</li>
<li>Garis: locus titik dengan jarak sama dari dua garis</li>
</ul>
<h3>Konstruksi dengan Jangka</h3>
<ol>
<li>Segitiga sama sisi: jangka dengan radius = sisi segitiga</li>
<li>Garis bagi sudut:busur di kedua kaki sudut</li>
<li> garis tengah-tengah: dua busur dari kedua ujung garis</li>
</ol>`
      }
    ]
  },
  {
    topic: 'G8-04 Statistics and Probability',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-04.1 Data Collection and Representation',
        content: `<h2>Data Collection and Representation</h2>
<p>Statistik adalah ilmu yang mempelajari cara mengumpulkan, menganalisis, dan menginterpretasi data.</p>
<h3>Jenis Data</h3>
<ul>
<li><strong>Data Kualitatif</strong>: Tidak berupa angka (misal: warna, nama)</li>
<li><strong>Data Kuantitatif</strong>: Berupa angka (misal: tinggi, berat)</li>
</ul>
<h3>Penyajian Data</h3>
<ul>
<li><strong>Tabel Frekuensi</strong>: Menyajikan data dalam bentuk tabel</li>
<li><strong>Histogram</strong>: Grafik batangan untuk data terkelompok</li>
<li><strong>Grafik Garis</strong>: Untuk data waktu</li>
<li><strong>Diagram Lingkaran</strong>: Untuk persentase</li>
<li><strong>Pictogram</strong>: Menggunakan gambar</li>
</ul>
<h3>Tabel Kontingensi</h3>
<p>Tabel untuk menyajikan dua variabel secara bersamaan.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-04.2 Measures of Central Tendency',
        content: `<h2>Measures of Central Tendency</h2>
<p>Ukuran pemusatan data menunjukkan nilai tengah dari data.</p>
<h3>1. Mean (Rata-rata)</h3>
<p>Mean = (Jumlah semua nilai) / (Banyaknya data)</p>
<p>Formula: x̄ = Σxᵢ / n</p>
<h3>2. Median (Nilai Tengah)</h3>
<p>Median adalah nilai yang membagi data menjadi dua bagian sama.</p>
<p>Untuk n ganjil: nilai tengah</p>
<p>Untuk n genap: rata-rata dua nilai tengah</p>
<h3>3. Modus (Mode)</h3>
<p>Modus adalah nilai yang paling sering muncul.</p>
<p>Data bisa tidak modus, uniklus, atau multimodus.</p>
<h3>Membandingkan</h3>
<p>Mean cocok untuk data tanpa pencilan.</p>
<p>Median cocok untuk data dengan pencilan.</p>
<p>Modus cocok untuk data kategorikal.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-04.3 Measures of Spread',
        content: `<h2>Measures of Spread</h2>
<p>Ukuran penyebaran menunjukkan seberapa tersebar data.</p>
<h3>1. Range (Rentang)</h3>
<p>Range = Nilai terbesar - Nilai terkecil</p>
<h3>2. Quartil</h3>
<ul>
<li><strong>Q1</strong>: Kuartil bawah (25% data)</li>
<li><strong>Q2</strong>: Median (50% data)</li>
<li><strong>Q3</strong>: Kuartil atas (75% data)</li>
</ul>
<h3>3. IQR (Interquartile Range)</h3>
<p>IQR = Q3 - Q1</p>
<h3>4. Box Plot (Diagram Kotak)</h3>
<p>Box plot menampilkan: min, Q1, median, Q3, max.</p>
<h3>5. Outlier (Data Pencilan)</h3>
<p>Outlier adalah data yang sangat berbeda dari lainnya.</p>
<p>Batas outlier:</p>
<ul>
<li>&lt; Q1 - 1.5 × IQR</li>
<li>&gt; Q3 + 1.5 × IQR</li>
</ul>`
      },
      {
        type: 'subject_matter',
        title: 'G8-04.4 Probability Basics',
        content: `<h2>Probability Basics</h2>
<p>Peluang adalah ukuran kemungkinan terjadinya suatu kejadian.</p>
<h3>Definisi Peluang</h3>
<p>P(A) = Banyak kejadian A / Banyak semua kemungkinan</p>
<h3>Ruang Sampel (S)</h3>
<p>Himpunan semua hasil yang mungkin.</p>
<h3>Kejadian (A)</h3>
<p>Himpunan bagian dari ruang sampel.</p>
<h3>Skala Peluang</h3>
<p>0 ≤ P(A) ≤ 1</p>
<ul>
<li>P(A) = 0: Mustahil</li>
<li>P(A) = 1: Pasti</li>
</ul>
<h3>Peluang Komplemen</h3>
<p>P(A') = 1 - P(A)</p>
<h3>公平 Experiments</h3>
<p>Eksperimen yang setiap hasilnya memiliki peluang sama.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-04.5 Probability of Combined Events',
        content: `<h2>Probability of Combined Events</h2>
<h3>Peluang Gabungan</h3>
<p>P(A ∪ B) = P(A) + P(B) - P(A ∩ B)</p>
<h3>Kejadian Saling Lepas (Mutually Exclusive)</h3>
<p>P(A ∩ B) = 0</p>
<p>P(A ∪ B) = P(A) + P(B)</p>
<h3>Kejadian Saling Bebas (Independent)</h3>
<p>P(A ∩ B) = P(A) × P(B)</p>
<h3>Diagram Venn</h3>
<p>Diagram Venn menampilkan hubungan antar himpunan.</p>
<h3>Peluang Komplemen</h3>
<p>P(A') = 1 - P(A)</p>
<h3>Contoh</h3>
<p>Peluang memilih kartu As atau kartu Warana dari dek kartu.</p>`
      }
    ]
  },
  {
    topic: 'G8-05 Algebraic Manipulation',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-05.1 Algebraic Expressions',
        content: `<h2>Algebraic Expressions</h2>
<p>Ekspresi aljabar adalah kombinasi variabel, konstanta, dan operasi.</p>
<h3>Komponen</h3>
<ul>
<li><strong>Variabel</strong>: Huruf yang mewakili bilangan (x, y, z)</li>
<li><strong>Konstanta</strong>: Bilangan tetap (1, 2, 3)</li>
<li><strong>Koefisien</strong>: Bilangan dikalikan variabel</li>
<li><strong>Suku</strong>: Bagian yang dijumlah/dikurangi</li>
</ul>
<h3>Suku Sejenis</h3>
<p>Suku dengan variabel dan pangkat yang sama.</p>
<p>Contoh: 3x dan 5x adalah suku sejenis.</p>
<h3>Menyederhanakan</h3>
<p>Gabungkan suku sejenis:</p>
<p>3x + 2x = 5x</p>
<p>7y - 2y = 5y</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-05.2 Algebraic Formulae',
        content: `<h2>Algebraic Formulae</h2>
<p>Rumus aljabar adalah persamaan yang menyatakan hubungan antar variabel.</p>
<h3>Substitusi</h3>
<p>Mengganti variabel dengan nilai tertentu.</p>
<p>Contoh: Jika A = πr², maka untuk r = 3, A = 9π</p>
<h3>Mengubah Subjek</h3>
<p>Rumus dapat diubah untuk mencari variabel tertentu.</p>
<p>Contoh: v = u + at</p>
<p>Untuk a: a = (v - u) / t</p>
<h3>Rumus Luas</h3>
<p>Persegi: L = s²</p>
<p>Segitiga: L = ½at</p>
<p>Lingkaran: L = πr²</p>
<h3>Rumus Volume</h3>
<p>Kubus: V = s³</p>
<p>Balok: V = p × l × t</p>
<p>Kerucut: V = ⅓πr²t</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-05.3 Linear Equations',
        content: `<h2>Linear Equations</h2>
<p>Persamaan linear adalah persamaan dengan pangkat variabel 1.</p>
<h3>Bentuk Umum</h3>
<p>ax + b = c</p>
<p>di mana a ≠ 0</p>
<h3>Penyelesaian</h3>
<ol>
<li>Kumpulkan suku yang sejenis</li>
<li>Pindahkan variabel ke satu sisi, konstanta ke sisi lain</li>
<li>Bagi dengan koefisien variabel</li>
</ol>
<h3>Contoh</h3>
<p>2x + 3 = 7</p>
<p>2x = 7 - 3</p>
<p>2x = 4</p>
<p>x = 2</p>
<h3>Persamaan dengan Tanda Kurung</h3>
<p>3(x + 2) = 12</p>
<p>3x + 6 = 12</p>
<p>3x = 6</p>
<p>x = 2</p>
<h3>Persamaan dengan Pecahan</h3>
<p>½x + 3 = 7</p>
<p>½x = 4</p>
<p>x = 8</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-05.4 Linear Inequalities',
        content: `<h2>Linear Inequalities</h2>
<p>Pertidaksamaan linear menggunakan tanda &lt;, &gt;, ≤, atau ≥.</p>
<h3>Sifat Pertidaksamaan</h3>
<p>Jika a &lt; b, maka:</p>
<ul>
<li>a + c &lt; b + c</li>
<li>a - c &lt; b - c</li>
<li>a × c &lt; b × c (jika c &gt; 0)</li>
<li>a × c &gt; b × c (jika c &lt; 0)</li>
</ul>
<h3>Penyelesaian</h3>
<p>Seperti persamaan, tapi:</p>
<p>Ketika mengali/ pembagian dengan bilangan negatif, tanda berubah!</p>
<h3>Contoh</h3>
<p>3x &lt; 12</p>
<p>x &lt; 4</p>
<p>-2x &lt; 8</p>
<p>x &gt; -4 (tanda berubah!)</p>
<h3>Grafik Penyelesaian</h3>
<p>x &lt; 4: titik 4 dengan anak panah ke kiri</p>
<p>x ≥ -4: titik -4 dengan anak panah ke kanan</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-05.5 Expanding and Factoring',
        content: `<h2>Expanding and Factoring</h2>
<h3>Distributif</h3>
<p>a(b + c) = ab + ac</p>
<p>Contoh: 3(x + 2) = 3x + 6</p>
<h3>Selisih Kuadrat</h3>
<p>a² - b² = (a + b)(a - b)</p>
<p>Contoh: x² - 9 = (x + 3)(x - 3)</p>
<h3>Faktorisasi</h3>
<p>Memecah ekspresi menjadi perkalian faktor.</p>
<p>x² + 5x + 6 = (x + 2)(x + 3)</p>
<h3>Langkah Faktorisasi</h3>
<ol>
<li>Cari dua bilangan yang hasil kalinya konstanta</li>
<li>Cari dua bilangan yang jumlahnya koefisien x</li>
</ol>
<h3>Contoh Faktorsasi</h3>
<p>x² + 7x + 12</p>
<p>= (x + 3)(x + 4) karena 3×4=12 dan 3+4=7</p>`
      }
    ]
  },
  {
    topic: 'G8-06 Number Skills and Indices',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-06.1 Integers and Operations',
        content: `<h2>Integers and Operations</h2>
<p>Bilangan bulat meliputi positif, negatif, dan nol.</p>
<h3>Bilangan Bulat (Z)</h3>
<p>Z = {..., -3, -2, -1, 0, 1, 2, 3, ...}</p>
<h3>Operasi Bilangan Bulat</h3>
<h4>Penjumlahan</h4>
<ul>
<li>(+3) + (+5) = +8</li>
<li>(-3) + (-5) = -8</li>
<li>(+3) + (-5) = -2</li>
</ul>
<h4>Pengurangan</h4>
<p>a - b = a + (-b)</p>
<p>(+5) - (+3) = +2</p>
<p>(+3) - (+5) = -2</p>
<h4>Perkalian</h4>
<ul>
<li>(+) × (+) = (+)</li>
<li>(-) × (-) = (+)</li>
<li>(+) × (-) = (-)</li>
</ul>
<h4>Pembagian</h4>
<p>Sama dengan perkalian.</p>
<h3>PEMDAS/BODMAS</h3>
<p>Parentheses, Exponents, Multiplication, Division, Addition, Subtraction</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-06.2 Indices and Powers',
        content: `<h2>Indices and Powers</h2>
<p>Indeks (pangkat/eksponen) menunjukkan perkalian berulang.</p>
<h3>Definisi</h3>
<p>aⁿ = a × a × a × ... × a (n kali)</p>
<h3>Hukum Indeks</h3>
<ol>
<li><strong>Perkalian</strong>: aᵐ × aⁿ = aᵐ⁺ⁿ</li>
<li><strong>Pembagian</strong>: aᵐ ÷ aⁿ = aᵐ⁻ⁿ</li>
<li><strong>Pangkat</strong>: (aᵐ)ⁿ = aᵐⁿ</li>
<li><strong> Perkalian Luar</strong>: (ab)ⁿ = aⁿbⁿ</li>
</ol>
<h3>Indeks Khusus</h3>
<ul>
<li><strong>a⁰ = 1</strong> (a ≠ 0)</li>
<li><strong>a⁻ⁿ = 1/aⁿ</strong></li>
</ul>
<h3>Contoh</h3>
<p>2³ × 2⁴ = 2⁷ = 128</p>
<p>5⁴ ÷ 5² = 5² = 25</p>
<p>(3²)³ = 3⁶ = 729</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-06.3 Standard Form',
        content: `<h2>Standard Form (Scientific Notation)</h2>
<p>Notasi ilmiah adalah cara menulis bilangan sangat besar atau kecil.</p>
<h3>Bentuk Umum</h3>
<p>a × 10ⁿ</p>
<p>di mana 1 ≤ |a| &lt; 10</p>
<h3>Bilangan Besar</h3>
<p>3000000 = 3 × 10⁶</p>
<p>450000000 = 4.5 × 10⁸</p>
<h3>Bilangan Kecil</h3>
<p>0.00003 = 3 × 10⁻⁵</p>
<p>0.0000015 = 1.5 × 10⁻⁶</p>
<h3>Operasi</h3>
<p>(3 × 10⁵) × (2 × 10³) = 6 × 10⁸</p>
<p>(6 × 10⁷) ÷ (2 × 10²) = 3 × 10⁵</p>
<h3>Aplikasi</h3>
<p>Astronomi (jarak antar bintang)</p>
<p>Fisika (ukuran atom)</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-06.4 Roots and Surds',
        content: `<h2>Roots and Surds</h2>
<h3>Akar Kuadrat</h3>
<p>√a = b bila b² = a</p>
<p>√16 = 4 karena 4² = 16</p>
<h3>Akar Tiga</h3>
<p>∛a = b bila b³ = a</p>
<p>∛27 = 3 karena 3³ = 27</p>
<h3>Surd</h3>
<p>Surd adalah akar yang tidak dapat disederhanakan menjadi bilangan bulat.</p>
<p>√2, √3, √5 adalah surd (irasional).</p>
<h3>Menyederhanakan Akar</h3>
<p>√50 = √(25 × 2) = 5√2</p>
<p>√72 = √(36 × 2) = 6√2</p>
<h3>Merasionalkan Penyebut</h3>
<p>1/√2 = √2/2</p>
<p>1/(√3) = √3/3</p>`
      }
    ]
  },
  {
    topic: 'G8-07 Ratio and Proportion',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-07.1 Ratio',
        content: `<h2>Ratio</h2>
<p>Perbandingan adalah hubungan antara dua besaran.</p>
<h3>Menulis Ratio</h3>
<p>a:b = a/b</p>
<p>Contoh: 3:5 = 3/5</p>
<h3>Ratio Sejenis</h3>
<p>Semakin besar nilai, semakin besar hasil.</p>
<p>Jika a:b = c:d, maka bilamana a tumbuh, c juga tumbuh.</p>
<h3>Ratio Berbalik Nilai</h3>
<p>Semakin besar nilai a, semakin kecil hasil c.</p>
<p>a:b = 1/c:1/d</p>
<h3>Menyederhanakan Ratio</h3>
<p>Bagi pembilang dan penyebut dengan FPB.</p>
<p>8:6 = 4:3</p>
<p>15:9 = 5:3</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-07.2 Proportion',
        content: `<h2>Proportion</h2>
<p>Proporsi adalah persamaan dua perbandingan.</p>
<h3>Bentuk</h3>
<p>a:b = c:d = e:f</p>
<h3>Perkalian Silang</h3>
<p>Jika a/b = c/d, maka ad = bc</p>
<h3>Menyelesaikan Proporsi</h3>
<p>x/4 = 6/8</p>
<p>8x = 24</p>
<p>x = 3</p>
<h3>Skala</h3>
<p>Skala = jarak pada peta / jarak sebenarnya</p>
<p>1:1000 berarti 1 cm = 1000 cm = 10 m</p>
<h3>Peta dan Model</h3>
<p>Skala digunakan untuk membuat peta dan model.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-07.3 Direct and Inverse Proportion',
        content: `<h2>Direct and Inverse Proportion</h2>
<h3>Perbandingan Langsung</h3>
<p>y = kx, di mana k konstan</p>
<p>Jika x dua kali, y dua kali.</p>
<p>Grafik: garis lurus melalui origin.</p>
<h3>Perbandingan Berbalik Nilai</h3>
<p>y = k/x</p>
<p>Jika x dua kali, y setengah.</p>
<p>Grafik: hiperbola</p>
<h3>Menyelesaikan Masalah</h3>
<p>Langsung: x₁/x₂ = y₁/y₂</p>
<p>Berbalik: x₁/x₂ = y₂/y₁</p>
<h3>Contoh</h3>
<p>5 orang menyelesaikan kerja dalam 8 hari.</p>
<p>10 orang: 8/2 = 4 hari (berbalik)</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-07.4 Percentage',
        content: `<h2>Percentage</h2>
<p>Persentase adalah perbandingan per 100.</p>
<h3>Definisi</h3>
<p>x% = x/100</p>
<h3>Pecahan ke Persentase</h3>
<ul>
<li>½ = 50%</li>
<li>¼ = 25%</li>
<li>¾ = 75%</li>
<li>⅕ = 20%</li>
</ul>
<h3>Desimal ke Persentase</h3>
<p>0.75 = 75%</p>
<p>0.05 = 5%</p>
<h3>Menghitung Persentase</h3>
<p>15% dari 200 = 30</p>
<p>(15/100) × 200 = 30</p>
<h3>Kenaikan/Penurunan</h3>
<p>Kenaikan 10% dari 50:</p>
<p>50 × 1.1 = 55</p>
<p>Penurunan 20% dari 80:</p>
<p>80 × 0.8 = 64</p>`
      }
    ]
  },
  {
    topic: 'G8-08 Sets',
    subtopics: [
      {
        type: 'subject_matter',
        title: 'G8-08.1 Introduction to Sets',
        content: `<h2>Introduction to Sets</h2>
<p>Himpunan adalah kumpulan objek yang terdefinisi dengan jelas.</p>
<h3>Notasi</h3>
<p>A = {1, 2, 3}</p>
<p>A = {x | x bilangan asli ≤ 3}</p>
<h3>Anggota</h3>
<p>1 ∈ A (1 adalah anggota A)</p>
<p>4 ∉ A (4 bukan anggota A)</p>
<h3>Jenis Himpunan</h3>
<ul>
<li><strong>Universal (S)</strong>: Himpunan semesta</li>
<li><strong>Kosong (∅)</strong>: Tidak memiliki anggota</li>
<li><strong>M Terbatas</strong>: Anggota terbatas</li>
<li><strong>Tak Terbatas</strong>: Anggota tak terbatas</li>
</ul>
<h3>Diagram Venn</h3>
<p>Diagram Venn menampilkan himpunan sebagai lingkaran.</p>
<p>Himpunan universal sebagai rectangle.</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-08.2 Operations on Sets',
        content: `<h2>Operations on Sets</h2>
<h3>Gabungan (Union)</h3>
<p>A ∪ B = {x | x ∈ A atau x ∈ B}</p>
<h3>Irisan (Intersection)</h3>
<p>A ∩ B = {x | x ∈ A dan x ∈ B}</p>
<h3>Komplemen</h3>
<p>A' = {x ∈ S | x ∉ A}</p>
<h3>Selisih</h3>
<p>A - B = {x | x ∈ A dan x ∉ B}</p>
<h3>Sifat</h3>
<ul>
<li>A ∪ ∅ = A</li>
<li>A ∩ ∅ = ∅</li>
<li>A ∪ A' = S</li>
<li>A ∩ A' = ∅</li>
</ul>
<h3>Hukum De Morgan</h3>
<p>(A ∪ B)' = A' ∩ B'</p>
<p>(A ∩ B)' = A' ∪ B'</p>`
      },
      {
        type: 'subject_matter',
        title: 'G8-08.3 Applications of Sets',
        content: `<h2>Applications of Sets</h2>
<h3>Masalah Sehari-hari</h3>
<p>Himpunan dapat digunakan untuk memecahkan masalah nyata.</p>
<h3>Diagram Venn Masalah</h3>
<p>Contoh: Dari 50 siswa, 30 senang Math, 25 senang Science, 10 senang keduanya.</p>
<p>Berapa yang senang minimal satu?</p>
<p>30 + 25 - 10 = 45</p>
<h3>Kardinalitas</h3>
<p>n(A) = banyak anggota A</p>
<p>n(A ∪ B) = n(A) + n(B) - n(A ∩ B)</p>
<h3>Aplikasi Statistik</h3>
<p>Himpunan digunakan dalam statistik untuk analisis data.</p>
<p>Misal: himpunan siswa dengan nilai &gt; 70</p>`
      }
    ]
  }
];

// Export for use
module.exports = {
  CLASS_URL,
  USERNAME,
  PIN,
  CURRICULUM
};

console.log('G8 NATIONAL PLUS Curriculum Data Ready');
console.log(`Total Topics: ${CURRICULUM.length}`);
console.log(`Total Subtopics: ${CURRICULUM.reduce((sum, t) => sum + t.subtopics.length, 0)}`);