####################################################################
#
# Copyright (c) 2023, Dmitri Ginzburg.  All Rights Reserved.
#
####################################################################

import os
import sys
import subprocess
import argparse
import maya.cmds as mc
import maya.standalone
import i4k_const as i4k
import maya.mel as mel

def getHW2RenderCommand(c_scene_path, c_out_dir, c_workspace, c_scene, c_episode, c_args_cam, c_args_textured):
    result = r'/usr/autodesk/maya2020/bin/Render -r hw2 -proj '+str(c_workspace)+r' -preRender "';
    result += r'string \$HOME = \"'+str(c_workspace)+r'\"; ';
    result += r'string \$OUT_DIR = \"'+str(c_out_dir)+r'\"; ';
    result += r'string \$SCENE = \"'+str(c_scene)+r'\"; ';
    result += r'string \$EPISODE = \"'+str(c_episode)+r'\"; ';
    result += r'string \$ARGS_CAM = \"'+str(c_args_cam)+r'\"; ';
    result += r'int \$ARG_TEXTURED = '+str(c_args_textured)+r'; ';
    result += r'workspace -o \$HOME; ';
    result += r'string \$cams[] = \`ls -type \"camera\"\`; string \$camName = \"\"; ';
    result += r'for(\$cam in \$cams){ setAttr(\$cam+\".rnd\", 0); if (startsWith(\$cam,\$EPISODE)){ \$camName = \$cam; }; }; ';
    result += r'if ( size(\$ARGS_CAM)>0 ){ if( \$ARGS_CAM != \"None\"){ \$camName = \$ARGS_CAM; }; } ';
    result += r'else if ( size(\$camName) == 0 ){ string \$splitName[] = stringToStringArray(\$SCENE,\"_\"); \$camName = \$EPISODE+\"_\"+(int)\$splitName[1]+\"Shape\"; }; ';
    result += r'print(\"tPlayblast for \"+\$SCENE+\" using camera \"+\$camName+\". Textured: \"+\$ARG_TEXTURED); ';
    result += r'setAttr(\$camName+\".rnd\", 1); ';
    result += r'setAttr \"defaultRenderGlobals.ren\" -type \"string\" \"mayaHardware2\"; ';
    result += r'setAttr \"defaultResolution.width\" 1920; ';
    result += r'setAttr \"defaultResolution.height\" 1080; ';
    result += r'setAttr \"defaultRenderGlobals.imageFormat\" 32; ';
    result += r'setAttr \"defaultRenderGlobals.outFormatControl\" 0; ';
    result += r'setAttr \"defaultRenderGlobals.animation\"  1; ';
    result += r'setAttr \"defaultRenderGlobals.putFrameBeforeExt\"  1; ';
    result += r'setAttr \"defaultRenderGlobals.extensionPadding\"  4; ';
    result += r'setAttr \"defaultRenderGlobals.byFrame\"  1; ';
    result += r'setAttr \"defaultRenderGlobals.byFrameStep\"  1; ';
    result += r'setAttr \"defaultRenderGlobals.startFrame\" \`playbackOptions -query -minTime\`; ';
    result += r'setAttr \"defaultRenderGlobals.endFrame\" \`playbackOptions -query -maxTime\`; ';
    result += r'setAttr \"defaultRenderGlobals.imageFilePrefix\" -type \"string\" \$OUT_DIR; ';
    result += r'setAttr \"defaultRenderGlobals.periodInExt\" 1; setAttr \"defaultRenderGlobals.useMayaFileName\" 0; ';
    result += r'setAttr \"hardwareRenderingGlobals.motionBlurEnable\" 0; ';
    result += c_scene_path;
    
    return result;

def getInt_(i):
    if i:
        return 1;
    else:
        return 0;

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Schedule render farm operations')
    parser.add_argument('-scene',     metavar='scene',     type=str,       nargs='?', help='Scene to playblast')
    parser.add_argument('-scene_version', metavar='scene_version',type=str,nargs='?', help='Scene version to playblast', default=None)
    parser.add_argument('-step',      metavar='step',      type=str,      nargs='?', help='Scene to playblast',          default='animation')
    parser.add_argument('-cam',       metavar='cam',       type=str,      nargs='?', help='Active camera')
    parser.add_argument('-out',       metavar='out',       type=str,      nargs='?', help='Output directory')
    parser.add_argument('-occlusion', metavar='occlusion', type=str2bool, nargs='?', help='Make an occlusion playblast', default="no")
    parser.add_argument('-textured',  metavar='textured',  type=str2bool, nargs='?', help='Display textures or not', default="yes")
    args = parser.parse_args()

    if not args.scene:
        print("ERROR: Scene is not provided.")
        exit(-1)

    scene = args.scene
    episode = scene.split('_')[0]

    scenePath =  i4k.getVersionedSceneLocation_(scene, stage=args.step, version=args.scene_version)
    if not os.path.exists(scenePath):
        print("Scene file not found: "+scenePath)
        exit(-1);
    print("\t\tINPUT PATH: "+scenePath)

    outPath = ""
    if args.out:
        outPath = args.out + '/'
    else:
        outPath = i4k.POUT+episode+'/'+scene
        if args.scene_version and args.scene_version != '':
            outPath += '_' + args.scene_version.lower()
        outPath += '/'+args.step.lower()+'/'

    if not os.path.exists(outPath):
        os.makedirs(outPath)
    print("\t\tOUTPUT PATH: "+outPath+scene)

    for f in os.listdir(outPath):
        os.remove(os.path.join(outPath, f))
    print("\t\tOUTPUT PATH cleanup complete")
    
    hw2command = getHW2RenderCommand(scenePath, outPath+scene, i4k.HOME, scene, episode, args.cam, getInt_(args.textured));

    playblast_process = subprocess.Popen(hw2command, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True );
    playblast_out,playblast_err = playblast_process.communicate();
    playblast_exicode = playblast_process.returncode;
    print(playblast_out);
    if str(playblast_exicode) != '0':
        print(playblast_err);
