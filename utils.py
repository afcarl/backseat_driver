import os
import glob
import math
import random
import numpy as np

from sklearn.utils import shuffle
from sklearn.preprocessing import LabelBinarizer
from sklearn.cross_validation import train_test_split
from sklearn.manifold import TSNE

from matplotlib import pyplot
from skimage.io import imshow, imsave, imread
from skimage.util import crop
from skimage import transform, filters, exposure, img_as_ubyte

import theano
from theano import tensor as T

import argparsing
args, unknown_args = argparsing.parse_args()

PIXELS = args.pixels
PAD_CROP = int(PIXELS * 0.125)
PAD_PIXELS = PIXELS + (PAD_CROP * 2)
imageSize = PIXELS * PIXELS
num_features = imageSize * 3

tsne = TSNE(verbose=1)

def load_train_cv(encoder, cache=False, relabel=False):
    if cache:
        X_train = np.load('data/cache/X_train_%d_f32.npy'%PIXELS)
        if relabel:
            y_train = np.load('data/cache/y_train_%d_f32_relabel.npy'%PIXELS)
        else:
            y_train = np.load('data/cache/y_train_%d_f32.npy'%PIXELS)
    else:
        X_train = []
        y_train = []
        print('Read train images')
        for j in range(10):
            print('Load folder c{}'.format(j))
            path = os.path.join('data', 'imgs', 'train', 'c' + str(j), '*.jpg')
            files = glob.glob(path)
            for fl in files:
                print fl
                img = imread(fl)
                img = transform.resize(img, output_shape=(PIXELS, PIXELS, 3), preserve_range=True)
                img = img.transpose(2, 0, 1)
                img = np.reshape(img, (1, num_features))
                X_train.append(img)
                y_train.append(j)

        X_train = np.array(X_train, dtype='float32')
        y_train = np.array(y_train)

        np.save('data/cache/X_train_%d_f32.npy'%PIXELS, X_train)
        np.save('data/cache/y_train_%d_f32.npy'%PIXELS, y_train)

    y_train = encoder.fit_transform(y_train).astype('int32')

    X_train, y_train = shuffle(X_train, y_train)

    X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size=0.15)

    X_train = X_train.reshape(X_train.shape[0], 3, PIXELS, PIXELS)
    X_test = X_test.reshape(X_test.shape[0], 3, PIXELS, PIXELS)

    # subtract per-pixel mean
    #pixel_mean = np.mean(X_train, axis=0)
    #np.save('data/pixel_mean_full_%d.npy'%PIXELS, pixel_mean)
    pixel_mean = np.load('data/pixel_mean_full_%d.npy'%PIXELS)
    X_train -= pixel_mean
    X_test -= pixel_mean

    return X_train, y_train, X_test, y_test, encoder

def load_train(encoder, cache=False, relabel=False):
    if cache:
        X_train = np.load('data/cache/X_train_%d_f32.npy'%PIXELS)
        if relabel:
            y_train = np.load('data/cache/y_train_%d_f32_relabel.npy'%PIXELS)
        else:
            y_train = np.load('data/cache/y_train_%d_f32.npy'%PIXELS)
    else:
        X_train = []
        y_train = []
        print('Read train images')
        for j in range(10):
            print('Load folder c{}'.format(j))
            path = os.path.join('data', 'imgs', 'train', 'c' + str(j), '*.jpg')
            files = glob.glob(path)
            for fl in files:
                print(fl)
                img = imread(fl)
                img = transform.resize(img, output_shape=(PIXELS, PIXELS, 3), preserve_range=True)
                img = img.transpose(2, 0, 1)
                img = np.reshape(img, (1, num_features))
                X_train.append(img)
                y_train.append(j)

        X_train = np.array(X_train, dtype='float32')
        y_train = np.array(y_train)

        np.save('data/cache/X_train_%d_f32.npy'%PIXELS, X_train)
        np.save('data/cache/y_train_%d_f32.npy'%PIXELS, y_train)

    y_train = encoder.fit_transform(y_train).astype('int32')

    X_train = X_train.reshape(X_train.shape[0], 3, PIXELS, PIXELS)

    # subtract pixel mean
    #pixel_mean = np.mean(X_train, axis=0)
    #np.save('data/pixel_mean_full_%d.npy'%PIXELS, pixel_mean)
    pixel_mean = np.load('data/pixel_mean.npy')
    X_train -= pixel_mean

    return X_train, y_train, encoder

def load_test(cache=False, size=PIXELS):
    if cache:
        X_test = np.load('data/cache/X_test_%d_f32.npy'%PIXELS)
        X_test_id = np.load('data/cache/X_test_id_%d_f32.npy'%PIXELS)
    else:
        print('Read test images')
        path = os.path.join('data', 'imgs', 'test', '*.jpg')
        files = glob.glob(path)
        X_test = []
        X_test_id = []
        for fl in files:
            print(fl)
            flbase = os.path.basename(fl)
            img = imread(fl)
            img = transform.resize(img, output_shape=(PIXELS, PIXELS, 3), preserve_range=True)
            img = img.transpose(2, 0, 1)
            img = np.reshape(img, (1, num_features))
            X_test.append(img)
            X_test_id.append(flbase)

        X_test = np.array(X_test, dtype='float32')
        X_test_id = np.array(X_test_id)

        np.save('data/cache/X_test_%d_f32.npy'%PIXELS, X_test)
        np.save('data/cache/X_test_id_%d_f32.npy'%PIXELS, X_test_id)

    X_test = X_test.reshape(X_test.shape[0], 3, PIXELS, PIXELS)

    # subtract pixel mean
    pixel_mean = np.load('data/pixel_mean_full_%d.npy'%PIXELS)
    X_test -= pixel_mean

    return X_test, X_test_id

def load_pseudo(cache=True, size=PIXELS):
    if cache:
        X_test = np.load('data/cache/X_test_%d_f32.npy'%PIXELS)
        pseudos = np.load('data/cache/X_test_pseudo.npy')
    else:
        # don't know why it wouldn't already be cached
        # if not add lines 123 to 136
        print 'what the heck?!'

    X_test = X_test.reshape(X_test.shape[0], 3, PIXELS, PIXELS)

    # subtract pixel mean
    pixel_mean = np.load('data/pixel_mean_full_%d.npy'%PIXELS)
    X_test -= pixel_mean

    return X_test, pseudos

def plot_sample(img):
    img = img.reshape(PIXELS, PIXELS, 3)
    imshow(img)
    #img = img / 290.
    pyplot.show(block=True)

def fast_warp(img, tf, output_shape, mode='nearest'):
    return transform._warps_cy._warp_fast(img, tf.params, output_shape=output_shape, mode=mode)

def batch_iterator_train(data, y, batchsize, train_fn):
    '''
    Data augmentation batch iterator for feeding images into CNN.
    Pads each image with 16 pixels on every side.
    Randomly crops image with original image shape from padded image. Effectively translating it.
    Randomly perturbs intensity of color channels by ~10 percent of intensity.
    Randomly perturbs brightness of image by 90-110%
    Random shears -5 to 5 degrees
    Random rotations -15 to 15 degrees
    '''
    n_samples = data.shape[0]
    data, y = shuffle(data, y)
    loss = []
    acc_train = 0.
    for i in range((n_samples + batchsize - 1) // batchsize):
        sl = slice(i * batchsize, (i + 1) * batchsize)
        X_batch = data[sl]
        y_batch = y[sl]

        # color intensity augmentation
        r_intensity = random.randint(0,1)
        g_intensity = random.randint(0,1)
        b_intensity = random.randint(0,1)
        intensity_scaler = random.randint(-20, 20)

        # pad and crop settings
        trans_1 = random.randint(0, (PAD_CROP*2))
        trans_2 = random.randint(0, (PAD_CROP*2))
        crop_x1 = trans_1
        crop_x2 = (PIXELS + trans_1)
        crop_y1 = trans_2
        crop_y2 = (PIXELS + trans_2)

        # shearing
        shear_deg = random.uniform(-5,5)

        # random rotations betweein -15 and 15 degrees
        dorotate = random.randint(-15,15)

        # brightness settings
        bright = random.uniform(0.9,1.1)

        # flip left-right choice
        #flip_lr = random.randint(0,1)

        # set the transform parameters for skimage.transform.warp
        # have to shift to center and then shift back after transformation otherwise
        # rotations will make image go out of frame
        center_shift   = np.array((PIXELS, PIXELS)) / 2. - 0.5
        tform_center   = transform.SimilarityTransform(translation=-center_shift)
        tform_uncenter = transform.SimilarityTransform(translation=center_shift)

        tform_aug = transform.AffineTransform(shear = np.deg2rad(shear_deg),
                                              rotation = np.deg2rad(dorotate))

        tform = tform_center + tform_aug + tform_uncenter

        # set empty copy to hold augmented images so that we don't overwrite
        X_batch_aug = np.copy(X_batch)

        # for each image in the batch do the augmentation
        for j in range(X_batch.shape[0]):
            # for each image channel
            for k in range(X_batch.shape[1]):
                X_batch_aug[j,k] = fast_warp(X_batch_aug[j,k], tform, output_shape=(PIXELS,PIXELS))
                # pad and crop images
                img_pad = np.pad(X_batch_aug[j,k], pad_width=((PAD_CROP,PAD_CROP), (PAD_CROP,PAD_CROP)), mode='constant')
                X_batch_aug[j,k] = img_pad[crop_x1:crop_x2, crop_y1:crop_y2]

                # flip left-right if chosen
                #if flip_lr == 1:
                #    X_batch_aug[j,k] = np.fliplr(X_batch_aug[j,k])

            if r_intensity == 1:
                X_batch_aug[j][0] += intensity_scaler
            if g_intensity == 1:
                X_batch_aug[j][1] += intensity_scaler
            if b_intensity == 1:
                X_batch_aug[j][2] += intensity_scaler

            # adjust brightness
            X_batch_aug[j] = X_batch_aug[j] * bright

        # fit model on each batch
        loss.append(train_fn(X_batch_aug, y_batch))

    return np.mean(loss)

def batch_iterator_train_pseudo_label(data, y, pdata, py, batchsize, pbatchsize, train_fn):
    '''
    Batch iterator for training wiht pseudo soft targets
    For total batch size 32, take 22 from train, and 10 from labeled test
    '''
    batchsize -= pbatchsize
    n_samples = data.shape[0]
    data, y = shuffle(data, y)
    pdata, py = shuffle(pdata, py)
    loss = []
    acc_train = 0.
    for i in range((n_samples + batchsize - 1) // batchsize):
        sl = slice(i*batchsize, (i+1) * batchsize)
        psl = slice(i*pbatchsize, (i+1) * pbatchsize)
        #X_batch = data[sl]
        #y_batch = y[sl]
        #pX_batch = pdata[psl]
        #py_batch = py[psl]
        X_batch = np.vstack((data[sl], pdata[psl]))
        y_batch = np.vstack((y[sl], py[psl]))
        X_batch, y_batch = shuffle(X_batch, y_batch)

        # color intensity augmentation
        r_intensity = random.randint(0,1)
        g_intensity = random.randint(0,1)
        b_intensity = random.randint(0,1)
        intensity_scaler = random.randint(-20, 20)

        # pad and crop settings
        trans_1 = random.randint(0, (PAD_CROP*2))
        trans_2 = random.randint(0, (PAD_CROP*2))
        crop_x1 = trans_1
        crop_x2 = (PIXELS + trans_1)
        crop_y1 = trans_2
        crop_y2 = (PIXELS + trans_2)

        # shearing
        shear_deg = random.uniform(-5,5)

        # random rotations betweein -15 and 15 degrees
        dorotate = random.randint(-15,15)

        # brightness settings
        bright = random.uniform(0.9,1.1)

        # flip left-right choice
        #flip_lr = random.randint(0,1)

        # set the transform parameters for skimage.transform.warp
        # have to shift to center and then shift back after transformation otherwise
        # rotations will make image go out of frame
        center_shift   = np.array((PIXELS, PIXELS)) / 2. - 0.5
        tform_center   = transform.SimilarityTransform(translation=-center_shift)
        tform_uncenter = transform.SimilarityTransform(translation=center_shift)

        tform_aug = transform.AffineTransform(shear = np.deg2rad(shear_deg),
                                              rotation = np.deg2rad(dorotate))

        tform = tform_center + tform_aug + tform_uncenter

        # set empty copy to hold augmented images so that we don't overwrite
        X_batch_aug = np.copy(X_batch)

        # for each image in the batch do the augmentation
        for j in range(X_batch.shape[0]):
            # for each image channel
            for k in range(X_batch.shape[1]):
                X_batch_aug[j,k] = fast_warp(X_batch_aug[j,k], tform, output_shape=(PIXELS,PIXELS))
                # pad and crop images
                img_pad = np.pad(X_batch_aug[j,k], pad_width=((PAD_CROP,PAD_CROP), (PAD_CROP,PAD_CROP)), mode='constant')
                X_batch_aug[j,k] = img_pad[crop_x1:crop_x2, crop_y1:crop_y2]

                # flip left-right if chosen
                #if flip_lr == 1:
                #    X_batch_aug[j,k] = np.fliplr(X_batch_aug[j,k])

            if r_intensity == 1:
                X_batch_aug[j][0] += intensity_scaler
            if g_intensity == 1:
                X_batch_aug[j][1] += intensity_scaler
            if b_intensity == 1:
                X_batch_aug[j][2] += intensity_scaler

            # adjust brightness
            X_batch_aug[j] = X_batch_aug[j] * bright

        # fit model on each batch
        loss.append(train_fn(X_batch_aug, y_batch))

    return np.mean(loss)

def batch_iterator_train_noaug(data, y, batchsize, train_fn):
    '''
    Batcher iterator for feeding images to CNN, no augmentations
    '''
    n_samples = data.shape[0]
    data, y = shuffle(data, y)
    loss = []
    acc_train = 0.
    for i in range((n_samples + batchsize - 1) // batchsize):
        sl = slice(i * batchsize, (i + 1) * batchsize)
        X_batch = data[sl]
        y_batch = y[sl]

        # fit model on each batch
        loss.append(train_fn(X_batch, y_batch))

    return np.mean(loss)

def batch_iterator_valid(data_test, y_test, batchsize, valid_fn):
    '''
    Batch iterator for testing network
    '''
    n_samples_valid = data_test.shape[0]
    loss_valid = []
    acc_valid = []
    for i in range((n_samples_valid + batchsize - 1) // batchsize):
        sl = slice(i * batchsize, (i + 1) * batchsize)
        X_batch_test = data_test[sl]
        y_batch_test = y_test[sl]

        loss_vv, acc_vv = valid_fn(X_batch_test, y_batch_test)
        loss_valid.append(loss_vv)
        acc_valid.append(acc_vv)

    # print statements for debugging, check if test images look like train images
    #plot_sample((X_batch_test[0] / np.amax(X_batch_test)))

    return np.mean(loss_valid), np.mean(acc_valid)
