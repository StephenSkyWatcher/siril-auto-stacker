# import os
# from pathlib import Path
# from .session import Session
# from .frame import Frame
# from pysiril.wrapper import *  # type: ignore

# from ..logger import Logger as _Logger

# Logger = _Logger(__name__)


# def convert(
#         Siril: Wrapper,  # type: ignore
#         session: Session,
#         frame: Frame,
#         delete_raws=False
# ):
#     try:
#         directories = [f"{session.working_dir}/{frame.dir}/"]

#         if session.multiple:
#             session.validate_supported(frame)
#             directories = session.getMultiNightDirectories(
#                 f"{session.working_dir}/{frame.dir}/")

#         for d in directories:
#             # Get the night name from the directory

#             if len(os.listdir(d)) == 0:
#                 Logger.info(f"No frames found in {d}")
#                 # Check process directory to see if frames have already been converted
#                 continue

#             night = d.replace(
#                 f"{session.working_dir}/{frame.dir}/{os.environ['MULTINIGHT_DIR_NAME']}", '')

#             Logger.info(f"Converting {frame.name}") if not session.multiple else Logger.info(
#                 f"Converting {frame.name} frames from: {night}")

#             Siril.cd(d)
#             conversion_name = frame.name if not session.multiple else f"{frame.name}_{night}"
#             out_directory = frame.process_dir if not session.multiple else f"../{frame.process_dir}"

#             [conversion_result] = Siril.convert(
#                 conversion_name,
#                 out=out_directory,
#                 fitseq=False)

#             if conversion_result is True:
#                 Logger.info(f"{frame.name} Frames Converted")

#                 if delete_raws:
#                     try:
#                         Logger.info(f"d: {d}")
#                         for filename in os.listdir(d):
#                             # TODO: Make this configurable
#                             # or better, compare to the fits results
#                             if filename.endswith(".cr3"):
#                                 os.remove(os.path.join(d, filename))
#                     except Exception as e:
#                         Logger.warning(
#                             f"Failed to delete raws for {frame.name} frames", e)
#             else:
#                 raise Exception()

#     except Exception as e:
#         raise Exception(f"Failed to Convert {frame.name} frames", e)
