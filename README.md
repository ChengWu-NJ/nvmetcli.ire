# nvmetcli增加nguid_bydev功能的开发记录

nvmetcli git clone from git://git.infradead.org/users/hch/nvmetcli.git commit:0a6b088 tag:v0.7

下面描述涉及的目录环境是 redhat/centos8.0，7.6，7.4。只支持python3.
git source: git clone [http://10.45.10.107/wucheng/nvmetcli.ire](http://10.45.10.107/wucheng/nvmetcli.ire)
## 基本原理

- nvme的target配置信息是记录在linux的configFS(/sys/kernel/config/nvmet)中。
- 运行在userspace中的配置程序可以通过在configFS中创建符合nvme target规范的目录，通知nvmet的内核创建相关的属性文件。
- 最后由配置程序修改属性文件完成相应的配置。
- nvmet内核模块在启动时会把/etc/nvmet/config.json的配置信息加载到configFS中。

```bash
/sys/kernel/config/nvmet
|-- hosts
|   `-- hostnqn
|-- ports
|   `-- 1
|       |-- addr_adrfam
|       |-- addr_traddr
|       |-- addr_treq
|       |-- addr_trsvcid
|       |-- addr_trtype
|       |-- referrals
|       `-- subsystems
|           `-- testnqn -> ../../../../nvmet/subsystems/testnqn
`-- subsystems
    `-- testnqn
        |-- allowed_hosts
        |   `-- hostnqn -> ../../../../nvmet/hosts/hostnqn
        |-- attr_allow_any_host
        |-- attr_serial
        |-- attr_version
        `-- namespaces
            |-- 1
            |   |-- device_nguid
            |   |-- device_path
            |   |-- device_uuid
            |   `-- enable
            `-- 2
                |-- device_nguid
                |-- device_path
                |-- device_uuid
                `-- enable
```
## nvmetcli的作用

- nvmetcli就是nvmet的配置程序，由python开发的命令行模式的。
- 除了增删改查configFS中信息的基本功能外，还可以将configFS的配置信息dump到/etc/nvmet/config.json，供nvmet内核模块下次启动时使用。
## 增加nguid_bydev功能的原因

- nvme target服务端的block设备盘没有设置有含义名称的属性，这是nvme规范缺少的。
- 如果用一个subsystem下只挂一个block设备，通过subsystem的目录名称来设置有含义的block盘名称，会导致大量的内存消耗。
## 使用方式
- rpm包文件在dist目录中。yum localinstall therpmfile
- 如果要将rpm加入os安装包中，请加入3个rpm依赖包 python3-configshell python3-kmod python3-six
- 和设置 nguid属性一样，在nsid的path下，使用命令 set device nguid_bydev=*somemeaningfuldevicename*
- ls 会同时显示 nguid和nguid_bydev两个属性的值。
 
```bash
]# nvmetcli ls
o- / ......................................................................................................................... [...]
  o- hosts ................................................................................................................... [...]
  | o- hostnqn ............................................................................................................... [...]
  o- ports ................................................................................................................... [...]
  | o- 2 .......................................................................... [trtype=rdma, traddr=10.45.69.206, trsvcid=4420]
  |   o- referrals ........................................................................................................... [...]
  |   o- subsystems .......................................................................................................... [...]
  o- subsystems .............................................................................................................. [...]
    o- testnqn ................................................................. [version=1.3, allow_any=1, serial=754185576f9eb188]
      o- allowed_hosts ....................................................................................................... [...]
      o- namespaces .......................................................................................................... [...]
        o- 1  [path=/dev/nvme0n1, uuid=a6c5b43b-fb42-471b-9bee-8f8818168627, nguid=61626364-6530-31ff-ffff-ffffffffffff, nguid_bydev=abcde01, disabled]
        o- 2  [path=/dev/abcde, uuid=a6dd1e70-7162-43ad-ae1c-daec43ac3d81, nguid=63616368-6564-6469-736b-313233343536, nguid_bydev=cacheddisk123456, disabled]
```
## 修改细节记录

- configFS中的属性文件由nvmet内核模块控制创建。在不修改nvmet代码的前提下，在nvmetcli增加一个代理命令set device nguid_bydev=有含义的block盘名称，在后端把block盘名称解码成uuid存入nguid属性文件。
- 增加一个nvme client解析target中block设备nguid取到有含义设备名称的python程序文件ecode_uuid.py，供udev设置rule时使用。

```bash
diff --git a/ecode_uuid.py b/ecode_uuid.py
new file mode 100644
index 0000000..6c25668
--- /dev/null
+++ b/ecode_uuid.py
@@ -0,0 +1,7 @@
+#!/usr/bin/python3
+
+import sys
+import nguidwithdev
+
+name= nguidwithdev.nguid2dev(sys.argv[1])
+print(name)
diff --git a/nguidwithdev.py b/nguidwithdev.py
new file mode 100644
index 0000000..dfd8d25
--- /dev/null
+++ b/nguidwithdev.py
@@ -0,0 +1,19 @@
+#!/usr/bin/python3
+
+def dev2nguid(dev):
+    _l = list(map(lambda x: x.rjust(2, '0'),
+            list(map(lambda x: x.split('x')[-1],
+            list(map(hex, list(map(ord, dev))))))))
+    _l.extend(['ff' for _ in range(16)])
+    return ''.join(_l[:4])+'-'+''.join(_l[4:6])\
+            +'-'+''.join(_l[6:8])+'-'+''.join(_l[8:10])\
+            +'-'+''.join(_l[10:16])
+
+
+def nguid2dev(guid):
+    _s = guid.replace('-', '')
+    _l = [_s[i:i+2] for i in range(0, len(_s), 2)]
+    return ''.join(list(map(chr, \
+            list(map(lambda x: int(x, 16), \
+            list(filter(lambda x: x!='ff', _l)) )) )) )
+
diff --git a/nvmetcli b/nvmetcli
index 3d8c16e..4f52678 100755
--- a/nvmetcli
+++ b/nvmetcli
@@ -26,6 +26,10 @@ import configshell_fb as configshell
 import nvmet as nvme
 from string import hexdigits
 import uuid
+import nguidwithdev
+
+dev2nguid = nguidwithdev.dev2nguid
+nguid2dev = nguidwithdev.nguid2dev


 def ngiud_set(nguid):
@@ -43,15 +47,31 @@ class UINode(configshell.node.ConfigNode):
         self.refresh()

     def _init_group(self, group):
+        def get_attr_wrap(self, attr):
+            if group=='device' and attr=='nguid_bydev':
+                return self.cfnode.get_attr('device', 'nguid')
+            else:
+                return self.cfnode.get_attr(group, attr)
+
         setattr(self.__class__, "ui_getgroup_%s" % group,
                 lambda self, attr:
-                    self.cfnode.get_attr(group, attr))
+                    get_attr_wrap(self, attr))
+
+        def set_attr_wrap(self, attr, value):
+            if group=='device' and attr=='nguid_bydev':
+                self.cfnode.set_attr('device', 'nguid', dev2nguid(value))
+            else:
+                self.cfnode.set_attr(group, attr, value)
+
         setattr(self.__class__, "ui_setgroup_%s" % group,
-                lambda self, attr, value:
-                    self.cfnode.set_attr(group, attr, value))
+                lambda self, attr, value: set_attr_wrap(self, attr, value))

         attrs = self.cfnode.list_attrs(group)
         attrs_ro = self.cfnode.list_attrs(group, writable=False)
+        #device group add aided attr -- nguid_bydev
+        if group == 'device':
+            attrs.append('nguid_bydev')
+
         for attr in attrs:
             writable = attr not in attrs_ro

@@ -59,6 +79,7 @@ class UINode(configshell.node.ConfigNode):
             t, d = getattr(self.__class__, name, {}).get(attr, ('string', ''))
             self.define_config_group_param(group, attr, t, d, writable)

+
     def refresh(self):
         self._children = set([])

@@ -214,6 +235,7 @@ class UINamespaceNode(UINode):
     ui_desc_device = {
         'path': ('string', 'Backing device path.'),
         'nguid': ('string', 'Namspace Global Unique Identifier.'),
+        'nguid_bydev': ('string', 'Setting nguid by meaningful device name'),
         'uuid': ('string', 'Namespace Universally Unique Identifier.'),
     }

@@ -280,6 +302,7 @@ class UINamespaceNode(UINode):
         ns_nguid = self.cfnode.get_attr("device", "nguid")
         if ngiud_set(ns_nguid):
             info.append("nguid=" + ns_nguid)
+            info.append("nguid_bydev=" + nguid2dev(ns_nguid))
         if self.cfnode.grpid != 0:
             info.append("grpid=" + str(self.cfnode.grpid))
         info.append("enabled" if self.cfnode.get_enable() else "disabled")
diff --git a/setup.py b/setup.py
index 1956d95..5936ab3 100755
--- a/setup.py
+++ b/setup.py
@@ -27,5 +27,5 @@ setup(
     maintainer_email = 'hch@lst.de',
     test_suite='nose2.collector.collector',
     packages = ['nvmet'],
-    scripts=['nvmetcli']
+    scripts=['nvmetcli', 'nguidwithdev.py', 'ecode_uuid.py']
     )

```



nvmetcli
========
This contains the NVMe target admin tool "nvmetcli".  It can either be
used interactively by invoking it without arguments, or it can be used
to save, restore or clear the current NVMe target configuration.

Installation
------------
Please install the configshell-fb package from
https://github.com/agrover/configshell-fb first.

nvmetcli can be run directly from the source directory or installed
using setup.py.

Common Package Dependencies and Problems
-----------------------------------------
Both python2 and python3 are supported via use of the 'python-six'
package.

nvmetcli uses the 'pyparsing' package -- running nvmetcli without this
package may produce hard-to-decipher errors.

Usage
-----
Look at Documentation/nvmetcli.txt for details.

Example NVMe Target .json files
--------------------------------------
To load the loop + explicit host version above do the following:

  ./nvmetcli restore loop.json

Or to load the rdma + no host authentication version do the following
after you've ensured that the IP address in rdma.json fits your setup:

  ./nvmetcli restore rdma.json

Or to load the fc + no host authentication version do the following
after you've ensured that the port traddr FC address information in
fc.json fits your setup:

  ./nvmetcli restore fc.json

These files can also be edited directly using your favorite editor.

Testing
-------
nvmetcli comes with a testsuite that tests itself and the kernel configfs
interface for the NVMe target.  To run it make sure you have nose2 and
the coverage plugin for it installed and simple run 'make test'.

Development
-----------------
Please send patches and bug reports to linux-nvme@lists.infradead.org for
review and acceptance.