import unittest
from rules import classify, permitted

class QualificationTests(unittest.TestCase):
    def test_ambiguous_replies_remain_unclassified(self):
        for text in ['sim', 'não', 'não operamos mais com banco, talvez voltemos', 'não sei se a empresa opera']:
            self.assertEqual(classify(text),'INCONCLUSIVO')
    def test_optout_precedes_sales_interest(self):
        self.assertEqual(classify('Não me mande mais propostas sobre taxas'),'OPT_OUT')
    def test_bank_does_not_become_generic_yes(self):
        self.assertEqual(classify('Operamos com banco.'),'OPERA_COM_BANCO')
    def test_no_sending_without_all_prerequisites(self):
        record={'reviewed':True,'consent_source':'Ligação autorizada','draft':'Olá','paused':False,'opted_out':False}
        self.assertTrue(permitted(record,False))
        self.assertFalse(permitted(record,True))
        for key,value in [('reviewed',False),('consent_source',''),('draft',' '),('paused',True),('opted_out',True)]:
            changed=record.copy();changed[key]=value
            self.assertFalse(permitted(changed,False),key)

if __name__=='__main__':unittest.main()
