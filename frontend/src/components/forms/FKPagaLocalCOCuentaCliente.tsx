/**
 * FKPagaLocalCOCuentaCliente - Cuenta Cliente contracts for Paga Local Colombia
 * Contains subtabs for: Aval Persona Jurídica, Aval Persona Natural, Sin Aval
 * Each subtab has 2 contract types: Crédito and Mandato
 */
import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Paper,
} from '@mui/material';
import {
  Business as BusinessIcon,
  Person as PersonIcon,
  Block as BlockIcon,
  Description as DescriptionIcon,
  Gavel as GavelIcon,
} from '@mui/icons-material';
import FKPagaLocalCOContractRequest from './FKPagaLocalCOContractRequest';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`cuenta-cliente-tabpanel-${index}`}
      aria-labelledby={`cuenta-cliente-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

// Contract type configurations
const CONTRACT_CONFIGS = {
  avalPJ: {
    title: 'Contratos Marco - Aval Persona Jurídica',
    description: 'Contratos para clientes con aval de Persona Jurídica',
    contracts: [
      {
        type: 'pl_co_credito_aval_pj',
        label: 'K° Crédito (Aval PJ)',
        description: 'Contrato de crédito con aval de Persona Jurídica',
        icon: <DescriptionIcon />,
      },
      {
        type: 'pl_co_mandato_pj',
        label: 'K° Mandato PJ',
        description: 'Contrato de mandato para Persona Jurídica',
        icon: <GavelIcon />,
      },
    ],
  },
  avalPN: {
    title: 'Contratos Marco - Aval Persona Natural',
    description: 'Contratos para clientes con aval de Persona Natural',
    contracts: [
      {
        type: 'pl_co_credito_aval_pn',
        label: 'K° Crédito (Aval PN)',
        description: 'Contrato de crédito con aval de Persona Natural',
        icon: <DescriptionIcon />,
      },
      {
        type: 'pl_co_mandato_pn',
        label: 'K° Mandato PN',
        description: 'Contrato de mandato para Persona Natural',
        icon: <GavelIcon />,
      },
    ],
  },
  sinAval: {
    title: 'Contratos Marco - Sin Aval',
    description: 'Contratos para clientes sin aval',
    contracts: [
      {
        type: 'pl_co_credito_no_aval',
        label: 'K° Crédito (No Aval)',
        description: 'Contrato de crédito sin aval',
        icon: <DescriptionIcon />,
      },
      {
        type: 'pl_co_mandato_no_aval',
        label: 'K° Mandato No Aval',
        description: 'Contrato de mandato sin aval',
        icon: <GavelIcon />,
      },
    ],
  },
};

interface ContractSelectorProps {
  config: typeof CONTRACT_CONFIGS.avalPJ;
  onSelectContract: (contractType: string, contractLabel: string) => void;
}

const ContractSelector: React.FC<ContractSelectorProps> = ({ config, onSelectContract }) => {
  return (
    <Box>
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.50', border: 1, borderColor: 'info.200' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'info.dark', mb: 1 }}>
          {config.title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {config.description}. Seleccione el tipo de contrato que desea solicitar.
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        {config.contracts.map((contract) => (
          <Grid size={{ xs: 12, md: 6 }} key={contract.type}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: 4,
                  borderColor: 'primary.main',
                },
                border: 1,
                borderColor: 'divider',
              }}
              onClick={() => onSelectContract(contract.type, contract.label)}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  {React.cloneElement(contract.icon, { sx: { fontSize: 48 } })}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  {contract.label}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {contract.description}
                </Typography>
                <Button variant="contained" size="small">
                  Solicitar
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const FKPagaLocalCOCuentaCliente: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedContract, setSelectedContract] = useState<{ type: string; label: string } | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
    setSelectedContract(null); // Reset selection when changing tabs
  };

  const handleSelectContract = (contractType: string, contractLabel: string) => {
    setSelectedContract({ type: contractType, label: contractLabel });
  };

  const handleBackToSelection = () => {
    setSelectedContract(null);
  };

  // If a contract is selected, show the request form
  if (selectedContract) {
    return (
      <Box>
        <Button
          variant="outlined"
          onClick={handleBackToSelection}
          sx={{ mb: 3 }}
        >
          ← Volver a selección de contratos
        </Button>
        <FKPagaLocalCOContractRequest
          contractType={selectedContract.type}
          contractLabel={selectedContract.label}
        />
      </Box>
    );
  }

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              minHeight: 64,
            },
          }}
        >
          <Tab
            label="Aval Persona Jurídica"
            icon={<BusinessIcon />}
            iconPosition="start"
          />
          <Tab
            label="Aval Persona Natural"
            icon={<PersonIcon />}
            iconPosition="start"
          />
          <Tab
            label="Sin Aval"
            icon={<BlockIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      <TabPanel value={currentTab} index={0}>
        <ContractSelector
          config={CONTRACT_CONFIGS.avalPJ}
          onSelectContract={handleSelectContract}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <ContractSelector
          config={CONTRACT_CONFIGS.avalPN}
          onSelectContract={handleSelectContract}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <ContractSelector
          config={CONTRACT_CONFIGS.sinAval}
          onSelectContract={handleSelectContract}
        />
      </TabPanel>
    </Box>
  );
};

export default FKPagaLocalCOCuentaCliente;
