# README.md

## Rice Disease Dataset

**Version:** v2.1
**Created:** July 2026
**Institution:** Kasetsart University

---

## 1. Dataset Description

This dataset contains images of rice leaves for rice disease classification.

* **Number of images:** 18,500
* **Number of classes:** 5
* **Image format:** JPG
* **Image size:** 512 × 512 pixels

---

## 2. Class Labels

| Label | Description      |
| ----- | ---------------- |
| 0     | Healthy          |
| 1     | Brown Spot       |
| 2     | Leaf Blast       |
| 3     | Bacterial Blight |
| 4     | Tungro           |

---

## 3. Dataset Structure

```text
dataset/

├── train/

├── validation/

├── test/

├── metadata.csv

└── labels.csv
```

---

## 4. Data Source

Images were collected from rice fields in Thailand between 2024 and 2025.

---

## 5. Annotation

* Annotated by two plant pathologists
* Annotation guideline version 1.2

---

## 6. Recommended Data Split

| Subset     | Percentage |
| ---------- | ---------: |
| Training   |        70% |
| Validation |        15% |
| Testing    |        15% |

---

## 7. Version History

| Version | Description                 |
| ------- | --------------------------- |
| v1.0    | Initial release             |
| v2.0    | Added new disease classes   |
| v2.1    | Corrected annotation errors |

---

## 8. Contact

Dr. Seksan Mathulaprangsan

Pattern REcognition and Computational InTElligence Laboratory (PRECITE Lab),
Department Computer Engineering,
Faculty of Engineering at Kamphaeng Saen,
Kasetsart University, Thailand,
E-mail: seksan.m@ku.th,
Tel: +66 65-976-xxxx

