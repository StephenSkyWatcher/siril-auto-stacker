import os
from typing import Optional
from glob import glob

from pysiril.siril import *  # type: ignore
from pysiril.wrapper import *  # type: ignore

from astropy import units as u
from astropy.coordinates import (ICRS, SkyCoord, get_icrs_coordinates)

from .frame import Frame
from .session import Session
from .preprocess import preprocess

from ..logger import Logger as _Logger

Logger = _Logger(__name__)


class SirilWrapper:
    def __init__(self,
                 sirilApp: Siril,  # type: ignore
                 sirilWrapper: Wrapper,  # type: ignore
                 session: Session,
                 remove_work: Optional[bool] = False,
                 target: Optional[str] = None
                 ) -> None:

        self.logger = Logger
        self.app = sirilApp  # Siril()  # type: ignore
        self.siril = sirilWrapper  # Wrapper(self.app)  # type: ignore
        self.session = session

        # self.session.working_dir = working_dir
        # self.session.lights = lights
        # self.session.darks = darks
        # self.biases = biases
        # self.session.flats = flats
        self.fits_extension = "fit"
        self.remove_work = remove_work
        self.to_remove = []

        self.target_ra_hms = None
        self.target_dec_dms = None
        self.target_ra = None
        self.target_dec = None
        self.constellation = None

        # self.get_target_data(target)

    def start(self):
        self.logger.info("Starting Siril")
        self.app.Open()
        self.siril.set16bits()
        self.siril.setext(self.fits_extension)
        self.siril.cd(self.session.working_dir)
        self.logger.info("Siril Started")

    def stop(self):
        self.logger.info("Closing Siril")
        self.app.Close()
        self.logger.info("Siril Closed")

        if self.remove_work:
            for f in self.to_remove:
                self.logger.info(f"Removing: {f}")
                # os.remove(f)

    def register(self, frame: Frame):

        try:
            if self.session.multiple:
                self.session.validate_supported(frame)

            nights = [f"{self.session.working_dir}/{frame.dir}/"] if not self.session.multiple else self.session.getMultiNightDirectories(
                f"{self.session.working_dir}/{frame.dir}/")

            for d in nights:
                # Get the night name from the directory
                night = d.replace(
                    f"{self.session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')
                self.logger.info(f"Calibrating {frame.name}") if not self.session.multiple else self.logger.info(
                    f"Calibrating {frame.name} frames from: {night}")

                self.logger.info(f"Registering {frame.name}")
                self.cd_process_dir(frame)

                register_name = f"{self.preprocess_prefix}{frame.name}" if not self.session.multiple else f"{self.preprocess_prefix}{frame.name}_{night}"

                GREEN_CHANNEL = 1

                self.siril.register(
                    register_name,
                    nostarlist=True,
                    layer=GREEN_CHANNEL,
                    pass2=True
                )

                self.siril.register(
                    register_name,
                    nostarlist=True,
                    prefix=self.registered_prefix,
                    layer=GREEN_CHANNEL,
                    drizzle=True,
                )

                # Work to be removed upon completion
                # preprocessed_work_file = f"{self.session.working_dir}/{frame.dir}/{self.preprocess_prefix}{frame.process_dir}/{frame.name}"
                # self.to_remove.append(
                #     f"{preprocessed_work_file}.{self.fits_extension}"
                # )

                self.logger.info(f"Registered {frame.name}")
        except Exception as e:
            raise (f"Failed to Register {frame.name} frames", e)

    def _stack(self, dir, frame: Frame, rmgreen=False):
        # Get the night name from the directory
        night = dir.replace(
            f"{self.session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')
        self.logger.info(f"Stacking {frame.name}") if not self.session.multiple else self.logger.info(
            f"Stacking {frame.name} frames from: {night}")

        self.cd_process_dir(frame)

        name_postfix = "" if frame == self.session.lights else f"_{night}" if night else ""

        self.logger.info(f"Stacking Name Post Fix: {name_postfix}")
        self.logger.info(f"Stacking Name: {frame.name}")

        if os.path.isfile(f"{self.registered_prefix}{self.preprocess_prefix}{frame.name}{name_postfix}.{self.fits_extension}"):
            stack_sequence = f"{self.registered_prefix}{self.preprocess_prefix}{frame.name}{name_postfix}"
        elif os.path.isfile(f"{self.registered_prefix}{frame.name}{name_postfix}.{self.fits_extension}"):
            stack_sequence = f"{self.registered_prefix}{frame.name}{name_postfix}"
        else:
            stack_sequence = f"{frame.name}{name_postfix}"

        stack_params = {
            "out": f"{frame.stacked_name}{name_postfix}",
            "type": "rej",
            'sigma_low': "3",
            'sigma_high': "3"
        }

        self.logger.info(f'Stack Sequence: {stack_sequence}')

        if (frame == self.session.biases):
            stack_params['norm'] = 'no'
            stack_params['rejection_type'] = "w"

        if (frame == self.session.darks):
            stack_params['norm'] = 'no'
            stack_params['rejection_type'] = "w"

        if (frame == self.session.flats):
            stack_params['norm'] = "mul"
            stack_params['rejection_type'] = "w"

        if (frame == self.session.lights):
            stack_params['norm'] = "addscale"
            stack_params['rejection_type'] = "l"
            stack_params['rgb_equal'] = True
            stack_params['filter_fwhm'] = "90%"
            stack_params['filter_round'] = "90%"

        """
        sequencename,
        type=None,
        rejection_type=None,
        sigma_low=3,
        sigma_high=3,
        norm=None,
        output_norm=False,
        rgb_equal=False,
        out=None,
        filter_fwhm=None,
        filter_wfwhm=None,
        filter_round=None,
        filter_bkg=None,
        filter_nbstars=None,
        filter_quality=None,
        filter_included=False,
        filter_incl=False,
        weight_from_noise=False,
        weight_from_nbstack=False,
        weight_from_nbstars=False,
        weight_from_wfwhm=False,
        fastnorm=False,
        rejmap=False,
        rejmaps=False
        """

        self.logger.info(
            f"Stack Parameters: {stack_sequence}, {stack_params}")

        self.siril.stack(stack_sequence, **stack_params)

        # Conditionally Remove Green Noise
        if rmgreen:
            self.siril.load(f"{frame.stacked_name}")
            self.siril.rmgreen()
            self.siril.save(f"{frame.stacked_name}")

        # Save Preview
        self.load_stacked_file(frame, night=night)
        self.siril.autostretch()
        self.siril.savejpg(
            f"{frame.stacked_name}{name_postfix}-preview")

        # Work to be removed upon completion
        try:
            for filename in os.listdir(f"{self.session.working_dir}/{frame.dir}/{frame.process_dir}"):
                # TODO: Make this configurable
                # or better, compare to the fits results
                if not filename.startswith(frame.stacked_name):
                    os.remove(os.path.join(
                        f"{self.session.working_dir}/{frame.dir}/{frame.process_dir}", filename))
        except Exception as e:
            Logger.warning(
                f"Failed to delete raws for {frame.name} frames", e)
        # Complete
        self.logger.info(f"Stacked {frame.name}")

    def stack(self, frame: Frame, rmgreen=False):
        try:
            if self.session.multiple:
                self.session.validate_supported(frame)

            nights = [f"{self.session.working_dir}/{frame.dir}/"] if not self.session.multiple else self.session.getMultiNightDirectories(
                f"{self.session.working_dir}/{frame.dir}/")

            if frame != self.session.lights:
                # Non-light stacking to get a stacked file for each night
                for d in nights:
                    self._stack(dir=d, frame=frame, rmgreen=rmgreen)
            else:
                self.cd_process_dir(frame)

                sequences = []
                for f in glob(f"{self.registered_prefix}{self.preprocess_prefix}{frame.name}*.seq"):
                    self.logger.info(f"Found: {f}")
                    sequences.append(f)

                self.logger.info(f"Sequences: {sequences}")
                # self.siril.merge('r_pp_light_1_.seq',
                #                  'r_pp_light_2_.seq', 'merged.seq')

                # self.siril.register(
                #     'merged',
                #     nostarlist=True,
                #     prefix=self.registered_prefix,
                #     layer=1,
                #     drizzle=True,
                # )

                # Light stacking to get a single stacked file for all nights
                """
                sequencename,
                type=None,
                rejection_type=None,
                sigma_low=3,
                sigma_high=3,
                norm=None,
                output_norm=False,
                rgb_equal=False,
                out=None,
                filter_fwhm=None,
                filter_wfwhm=None,
                filter_round=None,
                filter_bkg=None,
                filter_nbstars=None,
                filter_quality=None,
                filter_included=False,
                filter_incl=False,
                weight_from_noise=False,
                weight_from_nbstack=False,
                weight_from_nbstars=False,
                weight_from_wfwhm=False,
                fastnorm=False,
                rejmap=False,
                rejmaps=False
                """

                self.siril.stack('r_merged', **{
                    "out": f"{frame.stacked_name}_merged",
                    "type": "rej",
                    'sigma_low': "3",
                    'sigma_high': "3",
                    "norm": "addscale",
                    "rejection_type": "l",
                    "rgb_equal": True,
                    "filter_fwhm": "90%",
                    "filter_round": "90%"
                })
                # f"{self.session.working_dir}/{type.dir}/{type.process_dir}"

        except Exception as e:
            self.logger.error(f"Failed to Stack {frame.name}", e)
            return

    def cd_process_dir(self, frame: Frame):
        self.logger.info(
            f"Changing directory to {self.session.working_dir}/{frame.dir}/{frame.process_dir}")
        os.chdir(f"{self.session.working_dir}/{frame.dir}/{frame.process_dir}")
        self.siril.cd(self.session.working_dir)
        self.siril.cd(frame.dir)
        self.siril.cd(frame.process_dir)
        self.logger.info(f"Directory Changed")

    def load_stacked_file(self, frame: Frame, night=""):
        self.cd_process_dir(frame)
        stacked_file = self.session.get_stacked_file(frame, night=night)
        self.logger.debug(f"Loading Stacked File: {stacked_file}")
        self.siril.load(stacked_file)

    def get_target_data(self, target: str):
        # TODO: Consider looking at details.json
        # TODO: Make this more resiliant

        target_name = target if target is not None else os.path.basename(
            os.path.normpath(self.session.working_dir)).replace('_', " ")
        self.target = target_name

        try:
            coords = get_icrs_coordinates(
                name=self.target, parse=False, cache=False)
        except Exception as e:
            print(e)
            coords = None

        c = SkyCoord(
            ra=coords.ra.to(u.deg),
            dec=coords.dec.to(u.deg),
            frame=ICRS,
        ) if coords else None

        self.target_ra_hms = coords.ra.to_string(u.hour) if coords else None
        self.target_dec_dms = coords.dec.to_string(u.hour) if coords else None

        self.target_ra = coords.ra.value if coords else None
        self.target_dec = coords.dec.value if coords else None

        self.constellation = c.get_constellation() if c else None

        self.logger.info(f"Target: {self.target}")
        self.logger.info(f"Coords: {self.target_ra_hms} {self.target_dec_dms}")
        self.logger.info(f"Coords: {self.target_ra} {self.target_dec}")
        self.logger.info(f"Constellation: {self.constellation}")
