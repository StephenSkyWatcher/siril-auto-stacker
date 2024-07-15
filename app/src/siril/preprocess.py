import os
from pathlib import Path
from .session import Session
from .frame import Frame
from pysiril.wrapper import *  # type: ignore

from ..logger import Logger as _Logger

Logger = _Logger(__name__)


def convert(
    frame: Frame,
    session: Session,
    Siril: Wrapper,  # type: ignore
    night: str
):

    conversion_name = frame.name if not session.multiple else f"{frame.name}_{night}"

    Logger.info(f"Converting Frames {conversion_name}")

    out_directory = frame.process_dir if not session.multiple else f"../{frame.process_dir}"

    [conversion_result] = Siril.convert(
        conversion_name,
        out=out_directory,
        fitseq=False)

    if conversion_result is True:
        Logger.info(f"{frame.name} Frames Converted")
    return conversion_result


def preprocess(
        Siril: Wrapper,  # type: ignore
        session: Session,
        frame: Frame,
        delete_raws: bool = False
):
    try:
        directories = [f"{session.working_dir}/{frame.dir}/"]

        if session.multiple:
            session.validate_supported(frame)
            directories = session.getMultiNightDirectories(
                f"{session.working_dir}/{frame.dir}/")

        for d in directories:
            # Get the night name from the directory

            if len(os.listdir(d)) == 0:
                Logger.info(f"No frames found in {d}")
                # Check process directory to see if frames have already been converted
                continue

            night = d.replace(
                f"{session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')

            Logger.info(f"Converting {frame.name}") if not session.multiple else Logger.info(
                f"Converting {frame.name} frames from: {night}")

            Siril.cd(d)

            """
            Convert RAW to FITS
            """
            conversion_result = convert(frame, session, Siril, night)

            if conversion_result is True:
                if delete_raws:
                    try:
                        Logger.info(f"dir: {dir}")
                        for filename in os.listdir(dir):
                            # TODO: Make this configurable
                            # or better, compare to the fits results
                            if filename.endswith(".cr3"):
                                os.remove(os.path.join(d, filename))
                    except Exception as e:
                        Logger.warning(
                            f"Failed to delete raws for {frame.name} frames", e)
            else:
                raise Exception()

            """
            Calibrate FITS
            """
            calibrate_params = {
                "cfa": True,
                "equalize_cfa": True,
                "all": True,
                "prefix": os.environ['PREPROCESS_PREFIX'],
                "sighi": 3,
                "siglo": 3,
            }

            if frame == session.lights:
                calibrate_params['debayer'] = True

                stacked_flats = session.get_stacked_file(
                    session.flats, night=night)
                Logger.info(
                    f"Calibrating {frame.name} frames using Stacked Flats: {stacked_flats}")

                stacked_darks = session.get_stacked_file(
                    session.darks, night=night)
                Logger.info(
                    f"Calibrating {frame.name} frames using Stacked Darks: {stacked_darks}")

                if stacked_darks:
                    calibrate_params["dark"] = stacked_darks
                    calibrate_params["cc"] = 'dark'

                if stacked_flats:
                    calibrate_params["flat"] = stacked_flats

            if frame == session.flats:
                stacked_biases = session.get_stacked_file(
                    session.biases, night=night)

                if stacked_biases:
                    calibrate_params["bias"] = stacked_biases

            Logger.info(f"Calibration Parameters: {calibrate_params}")
            sequence_name = f"{frame.name}" if not session.multiple else f"{frame.name}_{night}"

            [calibrate_result] = Siril.calibrate(
                sequence_name, **calibrate_params)

            if calibrate_result is True:
                Logger.info(f"{frame.name} Frames Converted")

    except Exception as e:
        raise Exception(f"Failed to Convert {frame.name} frames", e)


#     try:
#         directories = [f"{session.working_dir}/{frame.dir}/"]

#         if session.multiple:
#             session.validate_supported(frame)
#             directories = session.getMultiNightDirectories(
#                 f"{session.working_dir}/{frame.dir}/")

#         for d in directories:

#             if len(os.listdir(d)) == 0:
#                 Logger.info(f"No frames found in {d}")
#                 # Check process directory to see if frames have already been converted
#                 continue

#             night = d.replace(
#                 f"{session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')

#             Logger.info(f"Calibrating {frame.name}") if not session.multiple else Logger.info(
#                 f"Calibrating {frame.name} frames from: {night}")

#             Siril.cd(d)

#             calibrate_params = {
#                 "cfa": True,
#                 "equalize_cfa": True,
#                 "all": True,
#                 "prefix": os.environ['PREPROCESS_PREFIX'],
#                 "sighi": 3,
#                 "siglo": 3,
#             }

#             if frame == session.lights:
#                 calibrate_params['debayer'] = True

#                 stacked_flats = session.get_stacked_file(
#                     session.flats, night=night)
#                 Logger.info(
#                     f"Calibrating {frame.name} frames using Stacked Flats: {stacked_flats}")

#                 stacked_darks = session.get_stacked_file(
#                     session.darks, night=night)
#                 Logger.info(
#                     f"Calibrating {frame.name} frames using Stacked Darks: {stacked_darks}")

#                 if stacked_darks:
#                     calibrate_params["dark"] = stacked_darks
#                     calibrate_params["cc"] = 'dark'

#                 if stacked_flats:
#                     calibrate_params["flat"] = stacked_flats

#             if frame == session.flats:
#                 stacked_biases = session.get_stacked_file(
#                     session.biases, night=night)

#                 if stacked_biases:
#                     calibrate_params["bias"] = stacked_biases

#             Logger.info(f"Calibration Parameters: {calibrate_params}")
#             sequence_name = f"{frame.name}" if not session.multiple else f"{frame.name}_{night}"

#             [calibrate_result] = Siril.calibrate(
#                 sequence_name, **calibrate_params)

#             if calibrate_result is True:
#                 Logger.info(f"{frame.name} Frames Converted")

#                 # if delete_raws:
#                 # try:
#                 #     Logger.info(f"d: {d}")
#                 #     for filename in os.listdir(d):
#                 #         # TODO: Make this configurable
#                 #         # or better, compare to the fits results
#                 #         if filename.endswith(".cr3"):
#                 #             os.remove(os.path.join(d, filename))
#                 # except Exception as e:
#                 #     Logger.warning(
#                 #         f"Failed to delete raws for {frame.name} frames", e)
#             else:
#                 raise Exception()

#             Logger.info(f"{frame.name} Frames Calibrated")
#     except Exception as e:
#         raise Exception(f"Failed to Calibrate {frame.name} frames", e)


# # try:
#         #     if self.session.multiple:
#         #         self.session.validate_supported(frame)

#         #     nights = [f"{self.session.working_dir}/{frame.dir}/"] if not self.session.multiple else self.session.getMultiNightDirectories(
#         #         f"{self.session.working_dir}/{frame.dir}/")

#         #     for d in nights:
#         #         # Get the night name from the directory
#         #         night = d.replace(
#         #             f"{self.session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')
#         #         self.logger.info(f"Calibrating {frame.name}") if not self.session.multiple else self.logger.info(
#         #             f"Calibrating {frame.name} frames from: {night}")

#         #         self.cd_process_dir(frame)

#         #         calibrate_params = {
#         #             "cfa": True,
#         #             "equalize_cfa": True,
#         #             "all": True,
#         #             "prefix": self.preprocess_prefix,
#         #             "sighi": 3,
#         #             "siglo": 3,
#         #         }

#         #         if frame == self.session.lights:
#         #             calibrate_params['debayer'] = True

#         #             stacked_flats = self.session.get_stacked_file(
#         #                 self.session.flats, night=night)
#         #             self.logger.info(
#         #                 f"Calibrating {frame.name} frames using Stacked Flats: {stacked_flats}")

#         #             stacked_darks = self.session.get_stacked_file(
#         #                 self.session.darks, night=night)
#         #             self.logger.info(
#         #                 f"Calibrating {frame.name} frames using Stacked Darks: {stacked_darks}")

#         #             if stacked_darks:
#         #                 calibrate_params["dark"] = stacked_darks
#         #                 calibrate_params["cc"] = 'dark'

#         #             if stacked_flats:
#         #                 calibrate_params["flat"] = stacked_flats

#         #         if frame == self.session.flats:
#         #             stacked_biases = self.session.get_stacked_file(
#         #                 self.session.biases, night=night)

#         #             if stacked_biases:
#         #                 calibrate_params["bias"] = stacked_biases

#         #         self.logger.info(f"Calibration Parameters: {calibrate_params}")
#         #         sequence_name = f"{frame.name}" if not self.session.multiple else f"{frame.name}_{night}"
#         #         self.siril.calibrate(sequence_name, **calibrate_params)

#         #         # Work to be removed upon completion
#         #         # TODO: Adjust for self.session.multiple
#         #         # converted_work_file = f"{self.session.working_dir}/{frame.dir}/{frame.process_dir}/{frame.name}"
#         #         # self.to_remove.append(
#         #         #     f"{converted_work_file}.{self.fits_extension}"
#         #         # )
#         #         # self.to_remove.append(
#         #         #     f"{converted_work_file}_conversion.txt"
#         #         # )

#         #         self.logger.info(f"{frame.name} Frames Calibrated")
#         # except Exception as e:
#         #     raise Exception(f"Failed to Calibrate {frame.name} frames", e)
