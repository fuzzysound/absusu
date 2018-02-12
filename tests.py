from django.test import TestCase
from experimenter.models import Experiment, Group, Goal
from reward import KPI
from django.utils import timezone
from random import random


class KPITests(TestCase):

    def test_CTR_calcuation(self):

        Experiment.objects.create_test_experiments(1)
        Group.objects.create_test_groups(2)
        Goal.objects.create_test_goals()

        for ip in range(20):
            response = self.client.post('/useractions/', {'ip': str(ip), 'action': '0_view'}, format='json')

            if response.data['groups']['0'] == '0':
                if random() < 0.9:
                    self.client.post('/useractions/', {'ip': str(ip), 'action': '0_click'}, format='json')
            else:
                if random() < 0.3:
                    self.client.post('/useractions/', {'ip': str(ip), 'action': '0_click'}, format='json')

        kpi = KPI()
        ctr_0 = kpi.CTR('0', '0', '0', timezone.now().date())
        ctr_1 = kpi.CTR('0', '1', '0', timezone.now().date())
        print(ctr_0, ctr_1)
        self.assertGreater(ctr_0, ctr_1)