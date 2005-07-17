import os, sys, time


if os.fork(): sys.exit()

f = open("/tmp/test/root1", "w")
f.write("woot")
f.close()
print "Parent wrote"


if not os.fork():
    os.seteuid(502)
    f = open("/tmp/test/testu", "w")
    f.write("woot")
    f.close()
    print "Child wrote"
    sys.exit()
if not os.fork():
    os.seteuid(501)
    f = open("/tmp/test/will", "w")
    f.write("woot")
    f.close()
    print "Child wrote"
    sys.exit()

os.wait()

f = open("/tmp/test/root2", "w")
f.write("woot")
f.close()
print "Parent wrote"
sys.exit()

print "Parent wrote"
