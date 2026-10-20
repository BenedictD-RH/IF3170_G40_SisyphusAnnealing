# IF3170_G40_SisyphusAnnealing

Program optimasi **3D cargo packing** yang menentukan posisi dan orientasi paket (dimensi, nilai, berat, fragile, ETA) di dalam truk agar total nilai maksimal tanpa melanggar batasan.

**Algoritma:** Hill Climbing (Steepest, Sideways, Random Restart, Stochastic), Simulated Annealing, dan Genetic Algorithm.

## Setup

Requirement: Python 3.10+.

```bash    
pip install -r requirements.txt
```

## Menjalankan Program

Jalankan dari root repository:

```bash
python src/main.py
```

1. Isi nama file input pada kolom *Input Initial State File* (file berada di `input/`, mis. `input5.json`), lalu tekan Enter.
2. Opsional: klik **Random Initial State** untuk memulai dari state acak.
3. Pilih algoritma, atur parameternya, lalu klik **Run**.
4. Klik **Display Plot** untuk melihat grafik hasil. Tekan `R` untuk mereset kamera.

Ringkasan hasil dicatat di `output/result.txt`.

## Pengujian

```bash
python tests/run_all_tests.py               # unit test
python tests/run_all_tests.py --benchmark   # unit test + benchmark seluruh testcase
```

## Struktur Direktori

| Folder | Isi |
|---|---|
| `src/algorithm` | implementasi algoritma optimasi |
| `src/data_struct` | struktur data dan fungsi objektif |
| `src/view` | GUI dan plotter |
| `input/`, `output/` | testcase dan hasil |
| `tests/` | unit test dan benchmark |


## Anggota Kelompok
| Nama | NIM |
|---|---|
| Benedict Darrel Setiawan | 13524057 |
| Steven Tan | 13524060 |
| Faris Wirakusuma Triawan | 13524130 |

## Pembagian Tugas
| Tugas | NIM |
|---|---|
| Visualizer | 13524057 |
| Objective Function & Heuristic | 13524057 |
| Steepest Ascent Hill Climbing | 13524057 |
| Sideways Move Hill Climbing | 13524060 |
| Random Restart Hill Climbing | 13524130 |
| Stochastic Hill Climbing | 13524130 |
| Simulated Annealing | 13524130 |
| Genetic Algorithm | 13524060 |