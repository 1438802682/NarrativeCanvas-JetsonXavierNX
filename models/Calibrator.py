import os
from glob import glob

import cv2
import numpy as np
import tensorrt as trt

import pycuda.driver as cuda
from pycuda import gpuarray


class EntropyCalibrator2(trt.IInt8EntropyCalibrator2):

    def __init__(self, calibrationDataPath, nCalibration, inputShape, cacheFile):
        trt.IInt8EntropyCalibrator2.__init__(self)

        # Initialize CUDA device and context
        cuda.init()  # Initialize CUDA
        self.cuda_device = cuda.Device(0)  # Assuming using the first device
        self.cuda_context = self.cuda_device.make_context()

        self.imageList = glob(calibrationDataPath + "*.JPEG")[:500]
        self.nCalibration = nCalibration
        self.shape = inputShape  # (N,C,H,W)
        self.buffeSize = trt.volume(inputShape) * trt.float32.itemsize
        self.cacheFile = cacheFile
        self.dIn = gpuarray.zeros(self.buffeSize // np.float32().itemsize, dtype=np.float32)

        self.oneBatch = self.batchGenerator()

        print(int(self.dIn.ptr))

    def __del__(self):
        del self.dIn

        # Clean up CUDA context
        if self.cuda_context:
            self.cuda_context.pop()
            del self.cuda_context
            self.cuda_context = None

    def batchGenerator(self):
        # Ensure that the CUDA context is activated within this range
        self.cuda_context.push()
        try:
            for i in range(self.nCalibration):
                print("> calibration %d" % i)
                subImageList = np.random.choice(self.imageList, self.shape[0], replace=False)
                yield np.ascontiguousarray(self.loadImageList(subImageList))
        finally:
            self.cuda_context.pop()

    def loadImageList(self, imageList):
        res = np.empty(self.shape, dtype=np.float32)
        for i, imagePath in enumerate(imageList):
            img_bgr = cv2.imread(imagePath, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise FileNotFoundError(f"[ERROR] The image {imagePath} could not be found.")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (self.shape[2], self.shape[3]))
            img_preprocessed = img_resized.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img_preprocessed = (img_preprocessed - mean) / std
            res[i] = img_preprocessed.transpose(2, 0, 1) 
        return res

    def get_batch_size(self):  # necessary API
        # return self.shape[0]
        return 1

    def get_batch(self, nameList=None, inputNodeName=None):  # necessary API
        try:
            data = next(self.oneBatch)
            self.dIn.set(data)  # Copying data using PyCUDA's set method
            return [int(self.dIn.ptr)]
        except StopIteration:
            return None

    def read_calibration_cache(self):  # necessary API
        if os.path.exists(self.cacheFile):
            print("[INFO] Succeed finding cahce file: %s" % (self.cacheFile))
            with open(self.cacheFile, "rb") as f:
                cache = f.read()
                return cache
        else:
            print("[INFO] Failed finding int8 cache!")
            return

    def write_calibration_cache(self, cache):  # necessary API
        with open(self.cacheFile, "wb") as f:
            f.write(cache)
        print("[INFO] Succeed saving int8 cache!")
        return
    

class MinMaxCalibrator(trt.IInt8MinMaxCalibrator):

    def __init__(self, calibrationDataPath, nCalibration, inputShape, cacheFile):
        trt.IInt8MinMaxCalibrator.__init__(self)

        # Initialize CUDA device and context
        cuda.init()  # Initialize CUDA
        self.cuda_device = cuda.Device(0)  # Assuming using the first device
        self.cuda_context = self.cuda_device.make_context()

        self.imageList = glob(calibrationDataPath + "*.JPEG")[:500]
        self.nCalibration = nCalibration
        self.shape = inputShape  # (N,C,H,W)
        self.buffeSize = trt.volume(inputShape) * trt.float32.itemsize
        self.cacheFile = cacheFile
        self.dIn = gpuarray.zeros(self.buffeSize // np.float32().itemsize, dtype=np.float32)

        self.oneBatch = self.batchGenerator()

        print(int(self.dIn.ptr))

    def __del__(self):
        del self.dIn

        # Clean up CUDA context
        if self.cuda_context:
            self.cuda_context.pop()
            del self.cuda_context
            self.cuda_context = None

    def batchGenerator(self):
        # Ensure that the CUDA context is activated within this range
        self.cuda_context.push()
        try:
            for i in range(self.nCalibration):
                print("> calibration %d" % i)
                subImageList = np.random.choice(self.imageList, self.shape[0], replace=False)
                yield np.ascontiguousarray(self.loadImageList(subImageList))
        finally:
            self.cuda_context.pop()

    def loadImageList(self, imageList):
        res = np.empty(self.shape, dtype=np.float32)
        for i, imagePath in enumerate(imageList):
            img_bgr = cv2.imread(imagePath, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise FileNotFoundError(f"[ERROR] The image {imagePath} could not be found.")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (self.shape[2], self.shape[3]))
            img_preprocessed = img_resized.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img_preprocessed = (img_preprocessed - mean) / std
            res[i] = img_preprocessed.transpose(2, 0, 1) 
        return res

    def get_batch_size(self):  # necessary API
        # return self.shape[0]
        return 1

    def get_batch(self, nameList=None, inputNodeName=None):  # necessary API
        try:
            data = next(self.oneBatch)
            self.dIn.set(data)  # Copying data using PyCUDA's set method
            return [int(self.dIn.ptr)]
        except StopIteration:
            return None

    def read_calibration_cache(self):  # necessary API
        if os.path.exists(self.cacheFile):
            print("[INFO] Succeed finding cahce file: %s" % (self.cacheFile))
            with open(self.cacheFile, "rb") as f:
                cache = f.read()
                return cache
        else:
            print("[INFO] Failed finding int8 cache!")
            return

    def write_calibration_cache(self, cache):  # necessary API
        with open(self.cacheFile, "wb") as f:
            f.write(cache)
        print("[INFO] Succeed saving int8 cache!")
        return