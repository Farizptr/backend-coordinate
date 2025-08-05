print("Script started")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF warnings
print("About to import TensorFlow...")
import tensorflow as tf
print("TensorFlow imported!")