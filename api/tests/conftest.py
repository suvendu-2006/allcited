import os

# Prevent OpenMP and Tokenizer threadpool deadlocks / segfaults during full test runs
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
