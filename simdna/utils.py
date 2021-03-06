from __future__ import absolute_import, division, print_function
import numpy as np
from scipy.signal import correlate2d
from simdna.simulations import loaded_motifs

def get_pssm_scores(encoded_sequences, pssm):
    encoded_sequences = np.squeeze(encoded_sequences, axis=1)
    num_samples, num_bases, seq_length = np.shape(encoded_sequences)
    scores = np.ones((num_samples, num_bases, seq_length))
    for base_indx in range(num_bases):
        base_pssm = pssm[base_indx].reshape(1, len(pssm[0]))
        fwd_scores = correlate2d(
            encoded_sequences[:, base_indx, :], base_pssm, mode='same')
        rc_base_pssm = pssm[-(base_indx + 1), ::-1].reshape(1, len(pssm[0]))
        rc_scores = correlate2d(
            encoded_sequences[:, base_indx, :], rc_base_pssm, mode='same')
        scores[:, base_indx, :] = np.maximum(fwd_scores, rc_scores)

    return scores.sum(axis=1)


def get_motif_scores(encoded_sequences, motif_names,
                     max_scores=None, return_positions=False, GC_fraction=0.4):
    """
    Computes pwm log odds.

    Parameters
    ----------
    encoded_sequences : 4darray
    motif_names : list of strings
    max_scores : int, optional
    return_positions : boolean, optional
    GC_fraction : float, optional

    Returns
    -------
    (num_samples, seq_length, num_motifs) complete score array by default.
    If max_scores, (num_samples, num_motifs*max_scores) max score array.
    If max_scores and return_positions, (num_samples, 2*num_motifs*max_scores)
    array with max scores and their positions.
    """
    num_samples, _, _, seq_length = np.shape(encoded_sequences)
    scores = np.ones((num_samples, len(motif_names), seq_length))
    for j, motif_name in enumerate(motif_names):
        pwm = loaded_motifs.getPwm(motif_name).getRows().T
        log_pwm = np.log(pwm)
        gc_pwm = 0.5 * np.array([[1 - GC_fraction, GC_fraction,
                                  GC_fraction, 1 - GC_fraction]] * len(pwm[0])).T
        gc_log_pwm = np.log(gc_pwm)
        scores[:, j, :] = get_pssm_scores(
            encoded_sequences, log_pwm) - get_pssm_scores(encoded_sequences, gc_log_pwm)
    if max_scores is not None:
        sorted_scores = np.sort(scores)[:, :, ::-1][:, :, :max_scores]
        if return_positions:
            sorted_positions = scores.argsort()[:, :, ::-1][:, :, :max_scores]
            return np.concatenate((sorted_scores.reshape((num_samples, len(motif_names) * max_scores)),
                                   sorted_positions.reshape((num_samples, len(motif_names) * max_scores))),
                                  axis=1)
        else:
            return sorted_scores.reshape((num_samples, len(motif_names) * max_scores))
    else:
        return scores
