"""Qwen3-VL timestamped video input at pinned PAI fps/pixel limits."""
from wcomr.development_vqa import SYSTEM,question_text


def decode_video_input(processor, path):
    from qwen_vl_utils import process_vision_info
    message=[{'role':'user','content':[{'type':'video','video':str(path),'fps':2.0,'max_pixels':768*28*28}]}]
    images,videos,kwargs=process_vision_info(message,image_patch_size=processor.image_processor.patch_size,
        return_video_kwargs=True,return_video_metadata=True)
    if images is not None or len(videos)!=1 or kwargs!={'do_sample_frames':False}:
        raise ValueError('Unexpected Qwen timestamped video preprocessing')
    video,metadata=videos[0]
    if metadata['total_num_frames']!=93 or abs(metadata['fps']-16)>1e-6:
        raise ValueError('Video source frame count/fps differs')
    indices=[int(x) for x in metadata['frames_indices']]
    if len(indices)!=10 or indices[0]!=0 or indices[-1]!=92 or len(set(indices))!=10:
        raise ValueError('Unexpected fixed2fps sampled frame coverage')
    return video,metadata


def prepare_question(processor, question, video, metadata):
    messages=[{'role':'system','content':[{'type':'text','text':SYSTEM}]},
              {'role':'user','content':[{'type':'video','video':'LOCAL_VIDEO'}, {'type':'text','text':question_text(question)}]}]
    text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    return processor(text=[text],videos=[video],video_metadata=[metadata],do_sample_frames=False,return_tensors='pt')
