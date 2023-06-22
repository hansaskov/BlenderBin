# The new config inherits a base config to highlight the necessary modification
_base_ = '../instaboost/mask-rcnn_r50_fpn_instaboost-4x_coco.py'

## Resnet strickes back checkpoint
checkpoint = 'https://download.openmmlab.com/mmclassification/v0/resnet/resnet50_8xb256-rsb-a1-600e_in1k_20211228-20e21305.pth'  # noqa

## We can use the pre-trained Mask RCNN model to obtain higher performance
load_from = 'https://download.openmmlab.com/mmdetection/v2.0/resnet_strikes_back/mask_rcnn_r50_fpn_rsb-pretrain_1x_coco/mask_rcnn_r50_fpn_rsb-pretrain_1x_coco_20220113_174054-06ce8ba0.pth'

## MODEL
model = dict(
    # Change backbone to use the resnet strikes back checkpoint
    backbone=dict(
        init_cfg=dict(
            type='Pretrained', prefix='backbone.', checkpoint=checkpoint)),
    roi_head=dict(
        bbox_head=dict(num_classes=2), mask_head=dict(num_classes=2)))

# TRAINER
optim_wrapper = dict(
    optimizer=dict(_delete_=True, type='AdamW', lr=0.0004, weight_decay=0.05),
    paramwise_cfg=dict(norm_decay_mult=0., bypass_duplicate=True))

max_epochs = 4
train_cfg = dict(max_epochs=max_epochs)
default_hooks = dict(checkpoint=dict(max_keep_ckpts=max_epochs))


# DATASET
data_root = 'data/'
data_name = "ic_bin_train/"
metainfo = {
    'classes': ('1','2'),
}

train_dataloader = dict(
    batch_size=4,
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file= data_name + 'train_pbr/000000/scene_gt_coco.json',
        data_prefix=dict(img=data_name + 'train_pbr/000000/')))
val_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file=  data_name + 'val/000000/scene_gt_coco.json',
        data_prefix=dict(img= data_name + 'val/000000/')))
test_dataloader = dict(
    dataset=dict(
        data_root=data_root,
        metainfo=metainfo,
        ann_file= 'ic_bin_test/scene_gt_coco.json',
        data_prefix=dict(img= 'ic_bin_test/')))

val_evaluator = dict(ann_file=data_root + data_name + 'val/000000/scene_gt_coco.json')
test_evaluator = dict(
    ann_file=data_root + 'ic_bin_test/scene_gt_coco.json',
    format_only=False,
    outfile_prefix='results/icbin-test')
