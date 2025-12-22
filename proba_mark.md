# Attention Is All You Need

## Аннотация

The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.

## Введение

Recurrent neural networks, long short-term memory networks, and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems. The inherently sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths, as memory constraints limit batching across examples.

The attention mechanism has become an integral part of compelling sequence modeling and transduction models, allowing modeling of dependencies without regard to their distance in the input or output sequences.

## Предпосылки

The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU, ByteNet, and ConvS2S, all of which use convolutional neural networks as basic building blocks, computing hidden representations in parallel for all input and output positions.

Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence.

## Архитектура модели

Most competitive neural sequence transduction models have an encoder-decoder structure. The encoder maps an input sequence of symbol representations $(x_1, ..., x_n)$ to a sequence of continuous representations $\mathbf{z} = (z_1, ..., z_n)$. Given $\mathbf{z}$, the decoder then generates an output sequence $(y_1, ..., y_m)$ of symbols one element at a time.

The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder.

### Стек энкодера и декодера

**Энкодер:** Состоит из стека N = 6 идентичных слоев. Каждый слой имеет два под-слоя. Первый - это механизм многоголового самовнимания, а второй - простая позиционно-зависимая полносвязная feed-forward сеть.

**Декодер:** Также состоит из стека N = 6 идентичных слоев. В дополнение к двум под-слоям в каждом слое энкодера, декодер вставляет третий под-слой, который выполняет многоголовое внимание над выходом стека энкодера.

### Внимание

Функция внимания может быть описана как отображение запроса и набора пар ключ-значение на выход, где запрос, ключи, значения и выход являются векторами. Выход вычисляется как взвешенная сумма значений, где вес, назначаемый каждому значению, вычисляется функцией совместимости запроса с соответствующим ключом.

#### Масштабированное скалярное произведение внимания

Мы называем наше внимание "Scaled Dot-Product Attention". Вход состоит из запросов и ключей размерности $d_k$, и значений размерности $d_v$. Мы вычисляем скалярные произведения запроса со всеми ключами, делим каждое на $\sqrt{d_k}$, и применяем функцию softmax для получения весов на значения.

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

#### Многоголовое внимание

Вместо выполнения единственной функции внимания с $d_{\text{model}}$-мерными ключами, значениями и запросами, мы обнаружили преимущество в линейном проецировании запросов, ключей и значений $h$ раз с различными, изученными линейными проекциями в $d_k$, $d_k$ и $d_v$ размерности соответственно.

Многоголовое внимание позволяет модели совместно обращать внимание на информацию из различных подпространств представлений в разных позициях:

$$
\begin{aligned}
\text{MultiHead}(Q, K, V) &= \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O \\
\text{где head}_i &= \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)
\end{aligned}
$$

Где проекции являются матрицами параметров:
$W_i^Q \in \mathbb{R}^{d_{\text{model}} \times d_k}$, $W_i^K \in \mathbb{R}^{d_{\text{model}} \times d_k}$, $W_i^V \in \mathbb{R}^{d_{\text{model}} \times d_v}$ и $W^O \in \mathbb{R}^{hd_v \times d_{\text{model}}}$.

### Позиционно-зависимые feed-forward сети

Каждый слой в нашем энкодере и декодере содержит полностью связанную feed-forward сеть, которая применяется к каждой позиции отдельно и идентично. Это состоит из двух линейных преобразований с активацией ReLU между ними:

$$
\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2
$$

### Позиционное кодирование

Поскольку наша модель не содержит рекуррентности и сверток, чтобы модель могла использовать порядок последовательности, мы должны внедрить некоторую информацию об относительной или абсолютной позиции токенов в последовательности. Мы используем синусоидальные и косинусоидальные функции разных частот:

$$
\begin{aligned}
PE_{(pos,2i)} &= \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right) \\
PE_{(pos,2i+1)} &= \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)
\end{aligned}
$$

где $pos$ - позиция и $i$ - размерность.

## Эксперименты

### Данные для обучения и бенчмаркинг

Мы обучались на стандартном наборе данных WMT 2014 English-German, состоящем из около 4.5 миллионов пар предложений. Предложения кодировались с использованием byte-pair encoding. Для English-French мы использовали значительно больший набор данных WMT 2014 English-French, состоящий из 36M предложений.

### Результаты

На задаче перевода с английского на немецкий WMT 2014 Transformer достигает оценки BLEU 28.4, превосходя все ранее опубликованные модели.

| Модель | BLEU | Стоимость обучения (FLOPs) |
|--------|------|----------------------------|
| **Английский-Немецкий** | | |
| Transformer (base) | 27.3 | $3.3 \times 10^{18}$ |
| Transformer (big) | **28.4** | $2.3 \times 10^{19}$ |
| **Английский-Французский** | | |
| Transformer (base) | 38.1 | $3.3 \times 10^{18}$ |
| Transformer (big) | **41.8** | $2.3 \times 10^{19}$ |

| Модель | F1 Score |
|--------|----------|
| Transformer (4 слоя) | 91.3 |
| Transformer (8 слоя) | 91.7 |

## Заключение

Мы представили Transformer, первую модель трансдукции последовательностей, полностью основанную на механизмах внимания, заменяющую рекуррентные слои, наиболее часто используемые в архитектурах энкодер-декодер, на многоголовое самовнимание.

Для задач перевода Transformer может обучаться значительно быстрее, чем архитектуры, основанные на рекуррентных или сверточных слоях. Мы достигаем нового state of the art на задачах перевода WMT 2014 English-to-German и English-to-French.

Мы в восторге от будущего моделей на основе внимания и планируем применять их к другим задачам. Transformer особенно подходит для задач, связанных с большими входами и выходами, и мы планируем продолжить его развитие.

## Список литературы

- Vaswani, A. et al. "Attention Is All You Need". NeurIPS 2017.
- Devlin, J. et al. "BERT: Pre-training of Deep Bidirectional Transformers". ACL 2019.
- Brown, T. B. et al. "Language Models are Few-Shot Learners". NeurIPS 2020.