import numpy as np
import cv2
import copy
from scipy import optimize, ndimage
import pylab as plt
import warnings
import tqdm


def getpoints(data, numpoints=3):
    """
    Function to display the central image in a stack and prompt the user to
    choose three locations by mouse click.  Once three locations have been
    clicked, the window closes and the function returns the coordinates

    Args
    ----------
    data : Numpy array
        Tilt series datastack
    numpoints : integer
        Number of points to use in fitting the tilt axis

    Returns
    ----------
    coords : Numpy array
        array containing the XY coordinates selected interactively by the user
    """
    warnings.filterwarnings('ignore')
    plt.figure(num='Align Tilt', frameon=False)
    if len(data.shape) == 3:
        plt.imshow(data[np.int(data.shape[0]/2), :, :], cmap='gray')
    else:
        plt.imshow(data, cmap='gray')
    plt.title('Choose %s points for tilt axis alignment....' % str(numpoints))
    coords = np.array(plt.ginput(numpoints, timeout=0, show_clicks=True))
    plt.close()
    return coords


def rigid_ecc(stack, start, show_progressbar):
    """
    Function to compute the shifts necessary to spatially register a stack of
    images. Shifts are determined by the OpenCV findTransformECC algorithm.
    Shifts are then applied and the aligned stack is returned.

    Args
    ----------
    stack : Numpy array
        3-D numpy array containing the tilt series data
    start : integer
        Position in tilt series to use as starting point for the alignment.
        If None, the central projection is used.
    show_progressbar : boolean
        Enable/disable progress bar

    Returns
    ----------
    out : TomoStack object
        Spatially registered copy of the input stack

    """

    number_of_iterations = 1000
    termination_eps = 1e-3
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                number_of_iterations,  termination_eps)
    old_trans = np.array([[1., 0, 0], [0, 1., 0]])
    out = copy.deepcopy(stack)
    out.data = np.zeros(stack.data.shape, stack.data.dtype)
    shifts = out.data.shape[0]*[None]
    if start is None:
        start = np.argmin(np.abs(stack.axes_manager[0].axis))
    out.data[start, :, :] = stack.data[start, :, :]
    # noinspection PyTypeChecker
    shifts[start] = old_trans

    for i in tqdm.tqdm(range(start+1, stack.data.shape[0]),
                       disable=(not show_progressbar)):
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        (cc, trans) = cv2.findTransformECC(stack.data[i, :, :],
                                           stack.data[i-1, :, :],
                                           warp_matrix,
                                           cv2.MOTION_TRANSLATION,
                                           criteria)
        trans[:, 2] = trans[:, 2] + old_trans[:, 2]
        out.data[i, :, :] = cv2.warpAffine(stack.data[i, :, :],
                                           trans,
                                           stack.data[i, :, :].T.shape,
                                           flags=cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_CONSTANT,
                                           borderValue=0.0)
        shifts[i] = trans
        old_trans = trans

    if start != 0:
        old_trans = np.array([[1., 0, 0], [0, 1., 0]])
        for i in tqdm.tqdm(range(start-1, -1, -1),
                           disable=(not show_progressbar)):
            warp_matrix = np.eye(2, 3, dtype=np.float32)
            (cc, trans) = cv2.findTransformECC(stack.data[i, :, :],
                                               stack.data[i+1, :, :],
                                               warp_matrix,
                                               cv2.MOTION_TRANSLATION,
                                               criteria)
            trans[:, 2] = trans[:, 2] + old_trans[:, 2]
            out.data[i, :, :] = cv2.warpAffine(stack.data[i, :, :],
                                               trans,
                                               stack.data[i, :, :].T.shape,
                                               flags=cv2.INTER_LINEAR,
                                               borderMode=cv2.BORDER_CONSTANT,
                                               borderValue=0.0)
            shifts[i] = trans
            old_trans = trans
    if not out.original_metadata.has_item('shifts'):
        out.original_metadata.add_node('shifts')
    out.original_metadata.shifts = shifts
    print('Spatial registration by ECC complete')
    return out


def rigid_pc(stack, start, show_progressbar):
    """
    Function to compute the shifts necessary to spatially register a stack of
    images. Shifts are determined by the OpenCV phaseCorrelate algorithm.
    Shifts are then applied and the aligned stack is returned.

    Args
    ----------
    stack : Numpy array
        3-D numpy array containing the tilt series data
    start : integer
        Position in tilt series to use as starting point for the alignment.
        If None, the central projection is used.
    show_progressbar : boolean
        Enable/disable progress bar

    Returns
    ----------
    out : TomoStack object
        Spatially registered copy of the input stack
    """

    old_trans = np.array([[1., 0, 0], [0, 1., 0]])
    out = copy.deepcopy(stack)
    out.data = np.zeros(stack.data.shape, stack.data.dtype)
    shifts = out.data.shape[0]*[None]
    if start is None:
        start = np.argmin(np.abs(stack.axes_manager[0].axis))
    out.data[start, :, :] = stack.data[start, :, :]
    # noinspection PyTypeChecker
    shifts[start] = old_trans

    for i in tqdm.tqdm(range(start+1, stack.data.shape[0]),
                       disable=(not show_progressbar)):
        trans = np.array([[1., 0, 0], [0, 1., 0]])
        trans[:, 2] = cv2.phaseCorrelate(
            np.float64(stack.data[i, :, :]),
            np.float64(stack.data[i-1, :, :]))[0]\
            + old_trans[:, 2]
        out.data[i, :, :] = cv2.warpAffine(stack.data[i, :, :],
                                           trans,
                                           stack.data[i, :, :].T.shape,
                                           flags=cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_CONSTANT,
                                           borderValue=0.0)
        shifts[i] = trans
        old_trans = trans

    if start != 0:
        old_trans = np.array([[1., 0, 0], [0, 1., 0]])
        for i in tqdm.tqdm(range(start-1, -1, -1),
                           disable=(not show_progressbar)):
            trans = np.array([[1., 0, 0], [0, 1., 0]])
            trans[:, 2] = cv2.phaseCorrelate(
                np.float64(stack.data[i, :, :]),
                np.float64(stack.data[i+1, :, :]))[0] + old_trans[:, 2]

            out.data[i, :, :] = cv2.warpAffine(stack.data[i, :, :],
                                               trans,
                                               stack.data[i, :, :].T.shape,
                                               flags=cv2.INTER_LINEAR,
                                               borderMode=cv2.BORDER_CONSTANT,
                                               borderValue=0.0)
            shifts[i] = trans
            old_trans = trans
    if not out.original_metadata.has_item('shifts'):
        out.original_metadata.add_node('shifts')
    out.original_metadata.shifts = shifts
    print('Spatial registration by PC complete')
    return out


def tilt_correct(stack, offset=0, locs=None, output=True):
    """
    Function to perform automated determination of the tilt axis of a
    TomoStack by tracking the center of mass (CoM) and comparing it to the path
    expected for an ideal cylinder

    Args
    ----------
    stack : TomoStack object
        3-D numpy array containing the tilt series data
    offset : integer
        Not currently used
    locs : list
        Locations at which to perform the CoM analysis
    output : boolean
        Output alignment results to console after each iteration

    Returns
    ----------
    out : TomoStack object
        Copy of the input stack after rotation and translation to center and
        make the tilt axis vertical
    """
    def sinocalc(array, y):
        """
        Function to extract sinograms at stack positions chosen by user via
        getpoints() function and track the center of mass (com) as a function
        of angle for each.

        Args
        ----------
        array : Numpy array
            3-D numpy array containing the tilt series data
        y : Numpy array
            Array containing the coordinates selected by the user in
            getPoints()

        Returns
        ----------
        outvals : Numpy array
            Array containing the center of mass as a function of tilt for the
            selected sinograms
        """
        def center_of_mass(row):
            """
            Compute the center of mass for a row of pixels

            Args
            ----------
            row : Numpy array
                Row of pixels extracted from a sinogram

            Returns
            ----------
            value : float
                Center of mass of the input row
            """
            size = np.size(row)
            value = 0.0
            for j in range(0, size):
                value = value + row[j]*(j+1)
            value = value/np.sum(row)
            return value

        outvals = np.zeros([np.size(array, axis=0), 3])
        sinotop = array[:, :, y[0]]
        sinomid = array[:, :, y[1]]
        sinobot = array[:, :, y[2]]

        for k in range(array.shape[0]):
            outvals[k][0] = center_of_mass(sinotop[k, :])
            outvals[k][1] = center_of_mass(sinomid[k, :])
            outvals[k][2] = center_of_mass(sinobot[k, :])

        return outvals

    def fit_coms(thetas, coms):
        """
        Function to fit the motion of calculated centers-of-mass in a
        sinogram to a sinusoidal function: (r0-A*cos(tilt)-B*sin(tilt)) as
        would be expected for an ideal cylinder. Return the coefficient of
        the fit equation for use in fitTiltAxis

        Args
        ----------
        thetas : Numpy array
            Array containing the stage tilt at each row in the sinogram
        coms : Numpy array
            Array containing the calculated center of mass as a function of
            tilt for the sinogram

        Returns
        ----------
        coeffs : Numpy array
            Coefficients (r0 , A , and B) resulting from the fit
        """

        def func(x, r0, a, b):
            return r0 - a*np.cos(x)-b*np.sin(x)

        guess = (0.0, 0.0, 0.0)
        # noinspection PyTypeChecker
        coeffs, covars = optimize.curve_fit(func,
                                            thetas,
                                            np.int16(coms),
                                            guess)
        return coeffs

    def fit_tilt_axis(coords, vals):
        """
        Function to fit the coefficients calculated by fit_coms() at each of
        the three user chosen positions to a linear function to determine the
        necessary rotation to vertically align the tilt axis

        Args
        ----------
        coords : Numpy array
            Horizontal coordinates from which the sinograms were extracted
        vals : Numpy array
            Array containing the r0 coefficient calculated for each sinogram by
            fitCoMs

        Returns
        ----------
        coeffs : Numpy array
            Coefficients (m and b) resulting from the fit
        """

        def func(x, m, b):
            return m*x+b

        guess = [0.0, 0.0]
        # noinspection PyTypeChecker
        coeffs, covars = optimize.curve_fit(f=func, xdata=coords, ydata=vals,
                                            p0=guess)
        return coeffs

    data = stack.deepcopy()
    if locs is None:
        locs = np.int16(np.sort(getpoints(stack.data)[:, 0]))
    else:
        locs = np.int16(np.sort(locs))
    if output:
        print('\nCorrecting tilt axis....')
    tilts = stack.axes_manager[0].axis*np.pi/180
    xshift = 0
    tiltaxis = 0
    totaltilt = 0
    totalshift = 0
    count = 1

    while abs(tiltaxis) >= 1 or abs(xshift) >= 1 or count == 1:
        centers = sinocalc(data.data, locs)

        com_results = np.zeros([3, 3])
        com_results[0, :] = fit_coms(tilts, centers[:, 0])
        com_results[1, :] = fit_coms(tilts, centers[:, 1])
        com_results[2, :] = fit_coms(tilts, centers[:, 2])

        r = np.zeros(3)
        r[:] = com_results[:, 0]

        axis_fits = fit_tilt_axis(locs, r)
        tiltaxis = 180/np.pi*np.tanh(axis_fits[0])
        xshift = (axis_fits[1]/axis_fits[0]*np.sin(np.pi/180*tiltaxis))
        xshift = (data.data.shape[1]/2)-xshift - offset
        totaltilt += tiltaxis
        totalshift += xshift

        if output:
            print(('Iteration #%s' % count))
            print(('Calculated tilt correction is: %s' % str(tiltaxis)))
            print(('Calculated shift value is: %s' % str(xshift)))
        count += 1

        data = data.trans_stack(xshift=0, yshift=xshift, angle=tiltaxis)

    out = copy.deepcopy(data)
    out.data = np.transpose(data.data, (0, 2, 1))
    if output:
        print('\nTilt axis alignment complete')
    out.original_metadata.tiltaxis = totaltilt
    out.original_metadata.xshift = totalshift
    return out


def tilt_analyze(data, limit=10, delta=0.3, output=False,
                 show_progressbar=False):
    """
    Perform automated determination of the tilt axis of a TomoStack by
    measuring the rotation of the projected maximum image.  Maximum image is
    rotated postively and negatively, filterd using a Hamming window, and the
    rotation angle is determined by iterative histogram analysis

    Args
    ----------
    data : TomoStack object
        3-D numpy array containing the tilt series data
    limit : integer or float
        Maximum rotation angle to use for MaxImage calculation
    delta : float
        Angular increment for MaxImage calculation
    output : boolean
        Output alignment results to console after each iteration
    show_progressbar : boolean
        Enable/disable progress bar

    Returns
    ----------
    opt_angle : TomoStack object
        Calculated rotation to set the tilt axis vertical
    """

    def hamming(img):
        """
        Function to apply hamming window to the image to remove edge effects

        Args
        ----------
        img : Numpy array
            Input image
        Returns
        ----------
        out : Numpy array
            Filtered image
        """
        if img.shape[0] < img.shape[1]:
            center_loc = np.int32((img.shape[1]-img.shape[0])/2)
            img = img[:, center_loc:-center_loc]
            if img.shape[0] != img.shape[1]:
                img = img[:, 0:-1]
            h = np.hamming(img.shape[0])
            ham2d = np.sqrt(np.outer(h, h))
        elif img.shape[1] < img.shape[0]:
            center_loc = np.int32((img.shape[0]-img.shape[1])/2)
            img = img[center_loc:-center_loc, :]
            if img.shape[0] != img.shape[1]:
                img = img[0:-1, :]
            h = np.hamming(img.shape[1])
            ham2d = np.sqrt(np.outer(h, h))
        else:
            h = np.hamming(img.shape[0])
            ham2d = np.sqrt(np.outer(h, h))
        out = ham2d*img
        return out

    def find_score(im, angle):
        """
        Function to perform histogram analysis to measure the rotation angle

        Args
        ----------
        im : Numpy array
            Input image
        angle : float
            Angle by which to rotate the input image before analysis

        Returns
        ----------
        hist : Numpy array
            Result of integrating image along the vertical axis
        score : numpy array
            Score calculated from hist
        """
        im = ndimage.rotate(im, angle, reshape=False, order=3)
        hist = np.sum(im, axis=1)
        score = np.sum((hist[1:] - hist[:-1]) ** 2)
        return hist, score

    image = np.max(data.data, 0)
    rot_pos = ndimage.rotate(hamming(image), limit/2, reshape=False, order=3)
    rot_neg = ndimage.rotate(hamming(image), -limit/2, reshape=False, order=3)
    angles = np.arange(-limit, limit+delta, delta)
    scores_pos = []
    scores_neg = []
    for rotation_angle in tqdm.tqdm(angles, disable=(not show_progressbar)):
        hist_pos, score_pos = find_score(rot_pos, rotation_angle)
        hist_neg, score_neg = find_score(rot_neg, rotation_angle)
        scores_pos.append(score_pos)
        scores_neg.append(score_neg)

    best_score_pos = max(scores_pos)
    best_score_neg = max(scores_neg)
    pos_angle = -angles[scores_pos.index(best_score_pos)]
    neg_angle = -angles[scores_neg.index(best_score_neg)]
    opt_angle = (pos_angle+neg_angle)/2
    if output:
        print('Optimum positive rotation angle: {}'.format(pos_angle))
        print('Optimum negative rotation angle: {}'.format(neg_angle))
        print('Optimum positive rotation angle: {}'.format(opt_angle))
    return opt_angle


def align_to_other(stack, other):
    """
    Function to spatially register a TomoStack using a seres of shifts
    previously calculated
    on a separate data stack of the same size.

    Args
    ----------
    stack : TomoStack object
        TomoStack which was previously aligned
    other : TomoStack object
        TomoStack to be aligned

    Returns
    ----------
    out : TomoStack object
        Aligned copy of other TomoStack
    """
    out = copy.deepcopy(other)
    out.data = np.zeros(np.shape(other.data), dtype=other.data.dtype)

    shifts = None
    tiltaxis = 0
    xshift = 0

    if stack.original_metadata.has_item('shifts'):
        shifts = stack.original_metadata.shifts
        out.original_metadata.shifts = stack.original_metadata.shifts
    if stack.original_metadata.has_item('tiltaxis'):
        tiltaxis = stack.original_metadata.tiltaxis
        out.original_metadata.shifts = stack.original_metadata.tiltaxis
    if stack.original_metadata.has_item('xshift'):
        xshift = stack.original_metadata.xshift
        out.original_metadata.shifts = stack.original_metadata.xshift

    out.original_metadata.shifts = stack.original_metadata.shifts

    if shifts:
        for i in range(0, out.data.shape[0]):
            out.data[i, :, :] = cv2.warpAffine(other.data[i, :, :],
                                               shifts[i],
                                               other.data[i, :, :].T.shape,
                                               flags=cv2.INTER_LINEAR,
                                               borderMode=cv2.BORDER_CONSTANT,
                                               borderValue=0.0)
    if (tiltaxis != 0) or (xshift != 0):
        out = out.trans_stack(xshift=0, yshift=xshift, angle=tiltaxis)
        out.data = np.transpose(out.data, (0, 2, 1))
    print('TomoStack alignment applied')
    return out
