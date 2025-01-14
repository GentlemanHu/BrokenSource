import math
from numbers import Number
from typing import Tuple

from Broken import nearest


class BrokenResolution:

    @staticmethod
    def round(width: Number, height: Number, *, scale: Number=1) -> Tuple[int, int]:
        """FFmpeg likes multiples of 2, so let it be"""
        return (
            max(1, nearest(scale*width,  multiple=2, type=int, operator=round)),
            max(1, nearest(scale*height, multiple=2, type=int, operator=round))
        )

    @staticmethod
    def fitscar(
        ow: int,
        oh: int,
        nw: int=None,
        nh: int=None,
        mw: int=math.inf,
        mh: int=math.inf,
        sc: float=1.0,
        ar: float=None
    ) -> Tuple[int, int]:
        """(Fit), (Sc)ale and force (A)spect (R)atio on a base to target resolution

        This method solves the following problem:
            "A window is at some initial size (ow, oh) and a resize was asked to (nw, nh); what
            final resolution the window should be, optionally enforcing an aspect ratio (ar)?"

        To which, the behavior is as follows in the two branches:
            No aspect ratio (ar=None) is send:
                - Returns the original resolution overrided by any new (nw, nh)

            Aspect ratio (ar!=None) is send:
                - If any of the new (nw, nh) is missing, find the other based on the aspect ratio
                - Else, prioritize width changes, and downscale/upscale accordingly

        Notes
        -----
            - The resolution is rounded to the nearest multiple of 2, so FFmpeg is happy

        Parameters
        ----------
        ow
            Original width
        oh
            Original height
        nw
            Target width
        nh
            Target height
        mw
            Maximum width
        mh
            Maximum height
        sc
            Scale factor
        ar
            Force aspect ratio, if any

        Returns
        -------
        (int, int)
            The new best-fit width and height
        """
        (w, h) = ((nw or ow), (nh or oh))

        if (ar is None):
            pass

        else:
            # Build from width (W) or from height (H)
            W = (w, w/ar)
            H = (h*ar, h)

            # Pick the non missing component's
            if (nh is None):
                (w, h) = W
            elif (nw is None):
                (w, h) = H

            # Based on upscale or downscale
            elif (nw != ow):
                (w, h) = W
            elif (nh != oh):
                (w, h) = H
            else:
                (w, h) = (w, h)

        return BrokenResolution.round(w, h, scale=sc)
