# Experiments

## Training Data and Benchmarking

We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million sentence pairs. Sentences were encoded using byte-pair encoding. For English-French, we used the significantly larger WMT 2014 English-French dataset consisting of 36M sentences.

## Results

On the WMT 2014 English-to-German translation task, the Transformer achieves a BLEU score of 28.4, outperforming all previously published models. The results are shown in Table .

| **Model** | **BLEU** | **Training Cost (FLOPs)** |
| --- | --- | --- |
| **English-to-German** |  |  |
| Transformer (base) | 27.3 | $3.3 \times 10^{18}$ |
| Transformer (big) | **28.4** | $2.3 \times 10^{19}$ |
| \addlinespace
**English-to-French** |  |  |
| Transformer (base) | 38.1 | $3.3 \times 10^{18}$ |
| Transformer (big) | **41.8** | $2.3 \times 10^{19}$ |

| **Model** | **F1 Score** |
| --- | --- |
| Transformer (4 layers) | 91.3 |
| Transformer (8 layers) | 91.7 |
