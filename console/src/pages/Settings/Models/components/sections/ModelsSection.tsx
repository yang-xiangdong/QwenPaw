import { useState, useEffect, useMemo } from "react";
import { SaveOutlined } from "@ant-design/icons";
import { Select, Button, Card } from "@agentscope-ai/design";
import type { ModelSlotRequest } from "../../../../../api/types";
import api from "../../../../../api";
import { useTranslation } from "react-i18next";
import { useAppMessage } from "../../../../../hooks/useAppMessage";
import styles from "../../index.module.less";

interface ProviderLite {
  id: string;
  name: string;
  models?: Array<{ id: string; name: string }>;
  extra_models?: Array<{ id: string; name: string }>;
  base_url?: string;
  api_key?: string;
  is_custom: boolean;
  is_local?: boolean;
  require_api_key?: boolean;
  meta?: Record<string, unknown>;
}

interface SlotLite {
  provider_id?: string;
  model?: string;
}

interface ModelsSectionProps {
  providers: ProviderLite[];
  activeModels: {
    active_llm?: SlotLite;
    active_image_generation?: SlotLite;
  } | null;
  onSaved: () => void;
}

interface SlotCardProps {
  title: string;
  description: string;
  providers: ProviderLite[];
  currentSlot?: SlotLite;
  selectedProviderId?: string;
  selectedModel?: string;
  onProviderChange: (providerId: string) => void;
  onModelChange: (modelId: string) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  canSave: boolean;
  isActive: boolean;
}

function SlotCard({
  title,
  description,
  providers,
  currentSlot,
  selectedProviderId,
  selectedModel,
  onProviderChange,
  onModelChange,
  onSave,
  saving,
  canSave,
  isActive,
}: SlotCardProps) {
  const { t } = useTranslation();
  const chosenProvider = providers.find((p) => p.id === selectedProviderId);
  const modelOptions = [
    ...(chosenProvider?.models ?? []),
    ...(chosenProvider?.extra_models ?? []),
  ];
  const hasModels = modelOptions.length > 0;

  return (
    <Card className={styles.slotSection} title={title}>
      <div className={styles.slotForm}>
        <div className={styles.slotField}>
          <label className={styles.slotLabel}>{t("models.provider")}</label>
          <Select
            style={{ width: "100%" }}
            placeholder={t("models.selectProvider")}
            value={selectedProviderId}
            onChange={onProviderChange}
            options={providers.map((p) => ({
              value: p.id,
              label: p.name,
            }))}
          />
        </div>

        <div className={styles.slotField}>
          <label className={styles.slotLabel}>{t("models.model")}</label>
          <Select
            style={{ width: "100%" }}
            placeholder={
              hasModels ? t("models.selectModel") : t("models.addModelFirst")
            }
            disabled={!hasModels}
            showSearch
            optionFilterProp="label"
            value={selectedModel}
            onChange={onModelChange}
            options={modelOptions.map((m) => ({
              value: m.id,
              label: `${m.name} (${m.id})`,
            }))}
          />
        </div>

        <div
          className={styles.slotField}
          style={{ flex: "0 0 auto", minWidth: "120px" }}
        >
          <label className={styles.slotLabel} style={{ visibility: "hidden" }}>
            {t("models.actions")}
          </label>
          <Button
            type="primary"
            loading={saving}
            disabled={!canSave}
            onClick={() => void onSave()}
            block
            icon={<SaveOutlined />}
          >
            {isActive ? t("models.saved") : t("models.save")}
          </Button>
        </div>
      </div>
      <p className={styles.slotDescription}>{description}</p>
      {currentSlot?.provider_id && currentSlot?.model ? (
        <p className={styles.slotDescription}>
          {t("models.currentSelection", {
            defaultValue: "Current: {{provider}} / {{model}}",
            provider: currentSlot.provider_id,
            model: currentSlot.model,
          })}
        </p>
      ) : null}
    </Card>
  );
}

export function ModelsSection({
  providers,
  activeModels,
  onSaved,
}: ModelsSectionProps) {
  const { t } = useTranslation();
  const [saving, setSaving] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<
    string | undefined
  >(undefined);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(
    undefined,
  );
  const [selectedImageProviderId, setSelectedImageProviderId] = useState<
    string | undefined
  >(undefined);
  const [selectedImageModel, setSelectedImageModel] = useState<
    string | undefined
  >(undefined);
  const [dirty, setDirty] = useState(false);
  const [imageDirty, setImageDirty] = useState(false);
  const { message } = useAppMessage();

  const currentSlot = activeModels?.active_llm;
  const currentImageSlot = activeModels?.active_image_generation;

  const eligible = useMemo(
    () =>
      providers.filter((p) => {
        const hasModels =
          (p.models?.length ?? 0) + (p.extra_models?.length ?? 0) > 0;
        if (!hasModels) return false;
        if (p.require_api_key === false) return !!p.base_url;
        if (p.is_custom) return !!p.base_url;
        if (p.require_api_key ?? true) return !!p.api_key;
        return true;
      }),
    [providers],
  );

  const imageEligible = useMemo(
    () =>
      eligible.filter((p) => {
        const imageGeneration = p.meta?.image_generation as
          | { enabled?: boolean }
          | undefined;
        return Boolean(imageGeneration?.enabled);
      }),
    [eligible],
  );

  useEffect(() => {
    if (currentSlot) {
      setSelectedProviderId(currentSlot.provider_id || undefined);
      setSelectedModel(currentSlot.model || undefined);
    }
    setDirty(false);
  }, [currentSlot?.provider_id, currentSlot?.model]);

  useEffect(() => {
    if (currentImageSlot) {
      setSelectedImageProviderId(currentImageSlot.provider_id || undefined);
      setSelectedImageModel(currentImageSlot.model || undefined);
    }
    setImageDirty(false);
  }, [currentImageSlot?.provider_id, currentImageSlot?.model]);

  const handleProviderChange = (pid: string) => {
    setSelectedProviderId(pid);
    setSelectedModel(undefined);
    setDirty(true);
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setDirty(true);
  };

  const handleImageProviderChange = (pid: string) => {
    setSelectedImageProviderId(pid);
    setSelectedImageModel(undefined);
    setImageDirty(true);
  };

  const handleImageModelChange = (model: string) => {
    setSelectedImageModel(model);
    setImageDirty(true);
  };

  const handleSave = async () => {
    if (!selectedProviderId || !selectedModel) return;

    const body: ModelSlotRequest = {
      provider_id: selectedProviderId,
      model: selectedModel,
      scope: "global",
      slot: "llm",
    };

    setSaving(true);
    try {
      await api.setActiveLlm(body);
      message.success(
        t("models.llmModelUpdated", {
          defaultValue: "LLM Model updated",
        }),
      );
      setDirty(false);
      onSaved();
    } catch (error) {
      const errMsg =
        error instanceof Error ? error.message : t("models.failedToSave");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleImageSave = async () => {
    if (!selectedImageProviderId || !selectedImageModel) return;

    const body: ModelSlotRequest = {
      provider_id: selectedImageProviderId,
      model: selectedImageModel,
      scope: "global",
      slot: "image_generation",
    };

    setSaving(true);
    try {
      await api.setActiveImageGeneration(body);
      message.success(
        t("models.imageModelUpdated", {
          defaultValue: "Image generation model updated",
        }),
      );
      setImageDirty(false);
      onSaved();
    } catch (error) {
      const errMsg =
        error instanceof Error ? error.message : t("models.failedToSave");
      message.error(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const isActive =
    currentSlot &&
    currentSlot.provider_id === selectedProviderId &&
    currentSlot.model === selectedModel;
  const canSave = dirty && !!selectedProviderId && !!selectedModel;

  const imageIsActive =
    currentImageSlot &&
    currentImageSlot.provider_id === selectedImageProviderId &&
    currentImageSlot.model === selectedImageModel;
  const canImageSave =
    imageDirty && !!selectedImageProviderId && !!selectedImageModel;

  return (
    <>
      <SlotCard
        title={t("models.defaultLlm", { defaultValue: "Default LLM" })}
        description={t("models.llmDescription", {
          defaultValue:
            "Set the global default LLM model from an authorized provider. You can choose a specific model for each Agent in the Chat page.",
        })}
        providers={eligible}
        currentSlot={currentSlot}
        selectedProviderId={selectedProviderId}
        selectedModel={selectedModel}
        onProviderChange={handleProviderChange}
        onModelChange={handleModelChange}
        onSave={handleSave}
        saving={saving}
        canSave={canSave}
        isActive={Boolean(isActive)}
      />
      <SlotCard
        title={t("models.defaultImage", {
          defaultValue: "Default Image Model",
        })}
        description={t("models.imageDescription", {
          defaultValue:
            "Set the global default image generation model. The generate_image tool will prefer this slot before falling back to the active LLM provider.",
        })}
        providers={imageEligible}
        currentSlot={currentImageSlot}
        selectedProviderId={selectedImageProviderId}
        selectedModel={selectedImageModel}
        onProviderChange={handleImageProviderChange}
        onModelChange={handleImageModelChange}
        onSave={handleImageSave}
        saving={saving}
        canSave={canImageSave}
        isActive={Boolean(imageIsActive)}
      />
    </>
  );
}
