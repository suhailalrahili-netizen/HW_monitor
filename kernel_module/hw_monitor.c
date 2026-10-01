#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/sched.h>
#include <linux/videodev2.h>
#include <sound/asound.h>
#include <linux/fs.h> 
#include <sound/pcm.h> 

static struct kprobe kp_cam = {
    .symbol_name = "v4l2_ioctl"
};

static int handler_cam(struct kprobe *p, struct pt_regs *regs)
{
    unsigned int cmd = regs->si;

    if (cmd == VIDIOC_STREAMON) {
        printk(KERN_INFO "[HW_MONITOR] DEVICE=CAMERA, PID=%d, NAME=%s, ACTION=RECORDING_STARTED\n", 
               current->tgid, current->group_leader->comm);
    }
    
    return 0;
}

static struct kprobe kp_mic = {
    .symbol_name = "snd_pcm_ioctl"
};

static int handler_mic(struct kprobe *p, struct pt_regs *regs)
{
    struct file *file = (struct file *)regs->di; 
    unsigned int cmd = regs->si; 

    if (cmd == SNDRV_PCM_IOCTL_START) {
        struct snd_pcm_file *pcm_file = file->private_data;
        
        if (pcm_file && pcm_file->substream) {
            if (pcm_file->substream->stream == SNDRV_PCM_STREAM_CAPTURE) {
                printk(KERN_INFO "[HW_MONITOR] DEVICE=MIC, PID=%d, NAME=%s, ACTION=RECORDING_STARTED\n", 
                       current->tgid, current->group_leader->comm);
            }
        }
    }
    
    return 0;
}

static int __init hw_monitor_init(void)
{
    int ret;

    kp_cam.pre_handler = handler_cam;
    ret = register_kprobe(&kp_cam);
    if (ret < 0) {
        printk(KERN_ERR "HW_MONITOR: Failed to register camera kprobe (%d)\n", ret);
        return ret;
    }
    printk(KERN_INFO "HW_MONITOR: Successfully planted camera kprobe at %s\n", kp_cam.symbol_name);

    kp_mic.pre_handler = handler_mic;
    ret = register_kprobe(&kp_mic);
    if (ret < 0) {
        printk(KERN_ERR "HW_MONITOR: Failed to register mic kprobe (%d)\n", ret);
        unregister_kprobe(&kp_cam); 
        return ret;
    }
    printk(KERN_INFO "HW_MONITOR: Successfully planted mic kprobe at %s\n", kp_mic.symbol_name);

    return 0;
}

static void __exit hw_monitor_exit(void)
{
    unregister_kprobe(&kp_cam);
    unregister_kprobe(&kp_mic);
    printk(KERN_INFO "HW_MONITOR: Unregistered all kprobes\n");
}

module_init(hw_monitor_init);
module_exit(hw_monitor_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Salman-Bander-Suhail");
MODULE_DESCRIPTION("Hardware Monitor tracking Camera and Mic via IOCTL");