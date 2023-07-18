## Setup Environment

* `conda` is not work for me, so I use `virtualenv` instead.

### Apple Silicon CPU

Install base TensorFlow, For TensorFlow version 2.13 or later:

```bash
python -m pip install tensorflow
```

Then install tensorflow-metal plug-in:

```bash
python -m pip install tensorflow-metal
```

`By default, tensorflow-metal will be not have in requirements.txt`

### Ubuntu without GPU

```bash
python -m pip install tensorflow
```
