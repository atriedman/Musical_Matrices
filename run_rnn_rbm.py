import tensorflow as tf
import numpy as np
import pandas as pd
import sys
sys.path.append("/Users/danshiebler/Documents")
import helper_functions as hf
import os
from tensorflow.python.ops import control_flow_ops
from tqdm import tqdm
from matplotlib import pyplot as plt
import glob
from copy import deepcopy
from tensorflow.examples.tutorials.mnist import input_data
import RBM
import rnn_rbm
import time

#clip gradients
#don't compute gradients on sample

def main(num_epochs, epochs_to_save, num_songs, path):
    train, generate = rnn_rbm.build_rnnrbm()
    x, sample, cost, params, size_bt = train()
    W, bh, bv, x, a, Wuh, Wuv, Wvu, Wuu, bu, u0 = params

    tf.scalar_summary("cost", cost) 
    hf.variable_summaries(W, "W")
    hf.variable_summaries(bh, "bh")
    hf.variable_summaries(bv, "bv")
    hf.variable_summaries(Wuh, "Wuh")
    hf.variable_summaries(Wuv, "Wuv")
    hf.variable_summaries(Wvu, "Wvu")
    hf.variable_summaries(Wuu, "Wuu")
    hf.variable_summaries(bu, "bu")
    hf.variable_summaries(u0, "u0")

    # optimizer = tf.train.AdamOptimizer(learning_rate=a)
    optimizer = tf.train.GradientDescentOptimizer(learning_rate=a)
    gvs = optimizer.compute_gradients(cost, [W, Wuh, Wuv, Wvu, Wuu, bh, bv, bu, u0])
    gvs = [(tf.clip_by_value(grad, -10., 10.), var) for grad, var in gvs]
    train_var = optimizer.apply_gradients(gvs)
    saver = tf.train.Saver()


    batch_size = 1000
    NUM_CORES = 4
    saved_weights_path = "/Users/danshiebler/Documents/Musical_Matrices/initializations/rbm.ckpt"
#     saved_weights_path = "/Users/danshiebler/Documents/Musical_Matrices/initializations/rbm_trained.ckpt"
#     saved_weights_path = "/Users/danshiebler/Documents/Musical_Matrices/initializations/rbm_trained_biaxial_100.ckpt"
#   data/Nottingham/all_C/
#   data/assorted_classical/classical_piano_C
#     songs = rnn_rbm.get_songs(path, num_songs)
    songs = rnn_rbm.get_songs_msgpack('data/song_msgpacks/biaxial_all_C', 1000)

    with tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=NUM_CORES,
                       intra_op_parallelism_threads=NUM_CORES)) as sess:
        init = tf.initialize_all_variables()
        sess.run(init)
        saver.restore(sess, saved_weights_path)

        merged = tf.merge_all_summaries()
        os.system("rm -rf /tmp/tf_rbm_logs/train")
        writer = tf.train.SummaryWriter('/tmp/tf_rbm_logs/train', sess.graph)

        # loop with batch
        print "starting"
        for epoch in range(num_epochs):
            costs = []
            start = time.time()
            for s_ind, song in enumerate(songs):
                for i in range(1, len(song), batch_size):
#                     print s_ind, i
                    tr_x = song[i:i + batch_size]
                    alpha = min(0.005, 0.05/float(i))
    #                 print "iteration: {}, shape: {}".format(i, tr_x.shape)
                    summary, _, C = sess.run([merged, train_var, cost], feed_dict={x: tr_x, a: alpha})
                    writer.add_summary(summary, i)
                    costs.append(C)
                if (s_ind % 100) == 0:
                    print "song: {} cost: {} time: {}".format(s_ind, np.mean(costs), time.time()-start)
            print "epoch: {} cost: {} time: {}".format(epoch, np.mean(costs), time.time()-start)
            print
            if (epoch + 1) % epochs_to_save == 0:
                save_path = saver.save(sess, "saved_data/rbm_rnn_epoch_{}".format(epoch))
#                 for i in range(10):
#                     generated_music = sess.run(generate(100), feed_dict={x: tr_x})
#                     save_path = "music_outputs/tf_training_iter/epoch_{}_composition_tf_{}.midi".format(epoch, i)
#                     rnn_rbm.write_song(save_path, generated_music)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])