import numpy as np
import gtsa


def mask_outliers_rate_of_change(x_values, y_values, threshold=100):
    """
    Returns mask for values that have an instantaneous rate of change (slope)
    greater than the threshold, e.g. 100 m/yr if x_values are in years (or decimal years)
    and y_values are in meters.
    """

    outliers_present = True

    x_values_tmp = list(x_values.copy())
    y_values_tmp = list(y_values.copy())

    while outliers_present:
        for j, v in enumerate(y_values_tmp):
            if j != len(y_values_tmp) - 1:
                y1 = y_values_tmp[j]
                y2 = y_values_tmp[j + 1]
                x1 = x_values_tmp[j]
                x2 = x_values_tmp[j + 1]
                m = (y2 - y1) / (x2 - x1)

                if abs(m) > threshold:
                    x_values_tmp.pop(j + 1)
                    y_values_tmp.pop(j + 1)
                    break
                else:
                    continue
            else:
                outliers_present = False
    mask = []
    for j in zip(x_values, y_values):
        if j in zip(x_values_tmp, y_values_tmp):
            mask.append(True)
        else:
            mask.append(False)

    mask = np.array(mask)
    return mask


def mask_outliers_gaussian_process(x_values, y_values, alpha_values):
    mask = np.ma.make_mask(x_values)
    masked_values = []
    kernel = gtsa.temporal.GPR_kernel_smoother()
    # kernel = gtsa.temporal.GPR_glacier_kernel()

    c = 0
    factor = 2
    while c == 0:
        gaussian_process_model = gtsa.temporal.GPR_model(
            x_values[mask], y_values[mask], kernel, alpha=alpha_values[mask]
        )

        mean_prediction, std_prediction = gtsa.temporal.GPR_predict(
            gaussian_process_model, x_values[mask]
        )

        diff = mean_prediction - y_values[mask]

        ### use standard deviation of prediction
        mask_tmp = np.greater(factor * std_prediction, np.abs(diff))
        if ~np.all(mask_tmp):
            masked_values.extend(y_values[mask][~mask_tmp])
            mask = []
            for j in y_values:
                if j in masked_values:
                    mask.append(False)
                else:
                    mask.append(True)
            mask = np.array(mask)
            factor = factor * 2
        else:
            c += 1

        ### use residuals
        ### mask where greater than standard deviation of residuals and repeat
        ### unless standard deviation of residuals less than 10
    #         if np.std(diff) > 10:
    #             mask_tmp = np.abs(diff) < np.std(diff)

    #             masked_values.extend(y_values[mask][~mask_tmp])

    #             mask = []
    #             for j in y_values:
    #                 if j in masked_values:
    #                     mask.append(False)
    #                 else:
    #                     mask.append(True)
    #             mask = np.array(mask)
    #         else:
    #             c+=1
    return mask
