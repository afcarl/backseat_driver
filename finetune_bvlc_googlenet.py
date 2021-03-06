import gzip
import time
import pickle
import numpy as np

import theano
from theano import tensor as T

import lasagne
from lasagne.updates import nesterov_momentum, adam
from lasagne.layers import helper, DenseLayer
from lasagne.nonlinearities import softmax

from sklearn.preprocessing import LabelEncoder

from models import bvlc_googlenet
from models import ST_ResNet_FullPre, ResNet_FullPre, ResNet_FullPre_Wide
from utils import load_train_cv, batch_iterator_train, batch_iterator_valid, load_pseudo
from crossvalidation import load_cv_fold

from matplotlib import pyplot
import warnings
warnings.filterwarnings("ignore")

import argparsing
args, unknown_args = argparsing.parse_args()

#TODO: Get pixel mean or Whatever preproc values they used for GoogLeNet and ImageNet

# training params
experiment_label = args.label
ITERS = args.epochs
BATCHSIZE = args.batchsize

LR_SCHEDULE = {
    0: 0.001,
    10: 0.0001,
    20: 0.00001
}

PIXELS = 224
imageSize = PIXELS * PIXELS
num_features = imageSize

"""
Set up all theano functions
"""
X = T.tensor4('X')
Y = T.ivector('y')

# set up theano functions to generate output by feeding data through network, any test outputs should be deterministic
net = bvlc_googlenet(X)
# load network weights
d = pickle.load(open('data/pre_trained_weights/blvc_googlenet.pkl'))
helper.set_all_param_values(net['prob'], d['param values'])

# stack our own softmax onto the final layer
output_layer = DenseLayer(net['pool5/7x7_s1'], num_units=10, W=lasagne.init.HeNormal(), nonlinearity=softmax)

# standard output functions
output_train = lasagne.layers.get_output(output_layer)
output_test = lasagne.layers.get_output(output_layer, deterministic=True)

# set up the loss that we aim to minimize, when using cat cross entropy our Y should be ints not one-hot
loss = lasagne.objectives.categorical_crossentropy(output_train, Y)
loss = loss.mean()

# L2 regularization
all_layers = lasagne.layers.get_all_layers(output_layer)
l2_penalty = lasagne.regularization.regularize_layer_params(all_layers, lasagne.regularization.l2) * 0.0001
loss = loss + l2_penalty

# set up loss functions for validation dataset
valid_loss = lasagne.objectives.categorical_crossentropy(output_test, Y)
valid_loss = valid_loss.mean()

valid_acc = T.mean(T.eq(T.argmax(output_test, axis=1), Y), dtype=theano.config.floatX)

# get parameters from network and set up sgd with nesterov momentum to update parameters
l_r = theano.shared(np.array(LR_SCHEDULE[0], dtype=theano.config.floatX))
params = lasagne.layers.get_all_params(output_layer, trainable=True)
updates = nesterov_momentum(loss, params, learning_rate=l_r)

# set up training and prediction functions
train_fn = theano.function(inputs=[X,Y], outputs=loss, updates=updates)
valid_fn = theano.function(inputs=[X,Y], outputs=[valid_loss, valid_acc])

# set up prediction function
predict_proba = theano.function(inputs=[X], outputs=output_test)

'''
load training data and start training
'''
encoder = LabelEncoder()

train_X, train_y, test_X, test_y, encoder = load_train_cv(encoder, cache=True)
print 'Train shape:', train_X.shape, 'Test shape:', test_X.shape
print 'Train y shape:', train_y.shape, 'Test y shape:', test_y.shape
print np.amax(train_X), np.amin(train_X), np.mean(train_X)

# loop over training functions for however many iterations, print information while training
train_eval = []
valid_eval = []
valid_acc = []
best_acc = 0.0
try:
    for epoch in range(ITERS):
        # change learning rate according to schedules
        if epoch in LR_SCHEDULE:
            l_r.set_value(LR_SCHEDULE[epoch])
        # do the training
        start = time.time()

        train_loss = batch_iterator_train(train_X, train_y, BATCHSIZE, train_fn)
        train_eval.append(train_loss)

        valid_loss, acc_v = batch_iterator_valid(test_X, test_y, BATCHSIZE, valid_fn)
        valid_eval.append(valid_loss)
        valid_acc.append(acc_v)

        ratio = train_loss / valid_loss
        end = time.time() - start
        # print training details
        print 'iter:', epoch, '| TL:', np.round(train_loss,decimals=3), '| VL:', np.round(valid_loss,decimals=3), '| Vacc:', np.round(acc_v,decimals=3), '| Ratio:', np.round(ratio,decimals=2), '| Time:', np.round(end,decimals=1)

        if acc_v > best_acc:
            best_acc = acc_v
            best_params = helper.get_all_param_values(output_layer)

except KeyboardInterrupt:
    pass

print "Final Acc:", best_acc

# save weights
f = gzip.open('data/weights/%s_best.pklz'%experiment_label, 'wb')
pickle.dump(best_params, f)
f.close()

last_params = helper.get_all_param_values(output_layer)
f = gzip.open('data/weights/%s_last.pklz'%experiment_label, 'wb')
pickle.dump(last_params, f)
f.close()
