import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[1]/'tools/minimum_distance_independent.py';s=importlib.util.spec_from_file_location('independent',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Controls(unittest.TestCase):
 def test_every_field(self):
  for q in (3,4,5,7,8,9):
   for d in [dict(q=q,n=3,k=1,d=3,generator=['111']),dict(q=q,n=q,k=2,d=q-1,generator=['1'*q,''.join(map(str,range(q)))])]:self.assertEqual(m.check(d)['distance'],d['d'])
 def test_tetracode(self):self.assertEqual(m.check(dict(q=3,n=4,k=2,d=3,generator=['1011','0112']))['distance'],3)
 def test_corruption(self):
  base=dict(q=4,n=3,k=1,d=3,generator=['111'])
  for changes in [dict(modulus=[0,0,1]),dict(d=1),dict(generator=['444']),dict(k=2,generator=['111','111'])]:
   with self.assertRaises(ValueError):m.check(dict(base,**changes))
 def test_budget(self):
  with self.assertRaises(ValueError):m.check(dict(q=3,n=4,k=2,d=3,generator=['1011','0112']),1)
if __name__=='__main__':unittest.main()
